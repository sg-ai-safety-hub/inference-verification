from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import Body, FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from ..lib.inference import run_inference
from ..lib.signed_envelope import SignedEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse
from pathlib import Path


class Settings(BaseSettings):
    host_key: str
    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).parent / ".env"),
        dotenv_filtering="only_existing",
    )


env = Settings()  # type: ignore

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
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
    "status": "Ready",
    "request": None,
    "response": None,
}


@sio.event
async def connect(sid, environ, auth):
    # Send state on connect
    await sio.emit("state", state, to=sid)


@app.post("/request")
async def request_inference(
    signed_request: SignedEnvelope[InferenceRequest],
) -> SignedEnvelope[InferenceResponse]:
    # Unwrap and verify request
    request = signed_request.unwrap(key=env.host_key).payload

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

    # Sign and return response
    return SignedEnvelope.wrap(
        id=signed_request.data.id,  # Match ID
        payload=response,
        key=env.host_key,
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
