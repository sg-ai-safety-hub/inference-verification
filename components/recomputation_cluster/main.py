import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict
import socketio

from ..lib.inference import run_inference, wait_for_inference_ready
from ..lib.secure_envelope import SecureEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse, require_key


class Settings(BaseSettings):
    host_key: str  # decryption key for recomputation
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
    "status": "Loading",
    "request": None,
    "received_response": None,
    "recomputed_response": None,
    "verified": None,
}


@sio.event
async def connect(sid, environ, auth):
    # Send state on connect
    await sio.emit("state", state, to=sid)


@app.post("/verify")
async def verify_inference(
    secure_request: SecureEnvelope[InferenceRequest],
    secure_response: SecureEnvelope[InferenceResponse],
):
    # Decrypt and verify request and response
    request = secure_request.unwrap(key=env.host_key, direction="request").payload
    response = secure_response.unwrap(key=env.host_key, direction="response").payload

    # Broadcast the received request and response
    state["status"] = "Running"
    state["request"] = request.messages[-1].content
    state["received_response"] = response.response_text
    state["recomputed_response"] = None
    state["verified"] = None
    await sio.emit("state", state)

    # Recompute response
    print(f"Running recomputation for message: {request.messages[-1].content}")
    recomputed = await run_inference(request, on_chunk=log_chunk)

    # Compare responses
    print(f"Received response:   {response.response_text}")
    print(f"Recomputed response: {recomputed.response_text}")
    verified = recomputed.response_text == response.response_text
    print(f"Verification {"successful" if verified else "failed"}")

    # Broadcast the recomputed response and verification result
    state["status"] = "Done"
    state["recomputed_response"] = recomputed.response_text
    state["verified"] = verified
    await sio.emit("state", state)

    return {"verified": verified}


@app.post("/clear")
async def clear():
    # Reset to ready
    state["status"] = "Ready"
    state["request"] = None
    state["received_response"] = None
    state["recomputed_response"] = None
    state["verified"] = None
    await sio.emit("state", state)


# Stream results to dashboard
async def log_chunk(chunk: str):
    state["recomputed_response"] = (state["recomputed_response"] or "") + chunk
    await sio.emit("state", state)
