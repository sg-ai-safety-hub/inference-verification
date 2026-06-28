from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import Body, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from ..lib.inference import run_inference, wait_for_inference_ready
from ..lib.secure_envelope import SecureEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse, require_key
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path


class Settings(BaseSettings):
    host_key: str
    api_key: str
    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).parent / ".env"),
        dotenv_filtering="only_existing",
    )


env = Settings()  # type: ignore


async def load_inference():
    # Poll the inference server
    await wait_for_inference_ready(on_attempt=lambda: print("Waiting for inference server..."))
    state["status"] = "Ready"
    await sio.emit("state", state)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(load_inference())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(
    dependencies=[Depends(require_key(env.api_key))],
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],  # Handled by FastAPI
)
app.mount("/socket.io", socketio.ASGIApp(sio, socketio_path=""))


state = {
    "is_training": False,
    "status": "Loading",
    "request": None,
    "response": None,
}


@sio.event
async def connect(sid, environ, auth):
    # Send state on connect
    await sio.emit("state", state, to=sid)


@app.post("/request")
async def request_inference(
    secure_request: SecureEnvelope[InferenceRequest],
) -> SecureEnvelope[InferenceResponse]:
    # Decrypt and verify request
    request = secure_request.unwrap(key=env.host_key, direction="request").payload

    # Broadcast the received request
    state["status"] = "Running"
    state["request"] = request.messages[-1].content
    state["response"] = ""
    await sio.emit("state", state)

    # Compute response
    print("Received inference request:", request.messages[-1].content)
    response = await run_inference(
        request, on_chunk=log_chunk, simulate_training=lambda: state["is_training"]
    )
    print("Inference response:", response.response_text)

    # Broadcast the computed response
    state["status"] = "Done"
    state["response"] = response.response_text
    await sio.emit("state", state)

    # Encrypt and return response
    return SecureEnvelope.wrap(
        id=secure_request.id,  # Match ID
        payload=response,
        key=env.host_key,
        direction="response",
    )


# Stream results to dashboard
async def log_chunk(chunk: str):
    state["response"] = (state["response"] or "") + chunk
    await sio.emit("state", state)


@app.post("/set-training")
async def set_training(new: bool = Body()):
    state["is_training"] = new
    await sio.emit("state", state)


@app.post("/clear")
async def clear():
    # Reset to ready, preserving the training mode toggle
    state["status"] = "Ready"
    state["request"] = None
    state["response"] = None
    await sio.emit("state", state)
