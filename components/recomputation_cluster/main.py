from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from ..lib.signed_envelope import SignedEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse
from pathlib import Path


class Settings(BaseSettings):
    inference_url: str
    max_tokens: int
    model: str
    mock_inference: bool = False
    model_config = SettingsConfigDict(
        env_file=(".env"),
        dotenv_filtering="only_existing",
    )


env = Settings()  # type: ignore
client = OpenAI(base_url=env.inference_url, api_key="unused")

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
    "status": "Ready",
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
    signed_request: SignedEnvelope[InferenceRequest],
    signed_response: SignedEnvelope[InferenceResponse],
):
    # Unwrap request and response
    request = signed_request.data.payload
    response = signed_response.data.payload

    # Broadcast the received request and response
    state["status"] = "Running"
    state["request"] = request.messages[-1].content
    state["received_response"] = response.response_text
    state["recomputed_response"] = None
    state["verified"] = None
    await sio.emit("state", state)

    # Recompute response
    print(f"Running recomputation for message: {request.messages[-1].content}")
    recomputed = run_inference(request)

    # Compare responses
    print(f"Received response:   {response.response_text}")
    print(f"Recomputed response: {recomputed.response_text}")
    verified = recomputed.response_text == response.response_text
    if verified:
        print("Verification succeeded")
    else:
        print("Verification failed")

    # Broadcast the recomputed response and verification result
    state["status"] = "Done"
    state["recomputed_response"] = recomputed.response_text
    state["verified"] = verified
    await sio.emit("state", state)

    return {"verified": verified}


def run_inference(request: InferenceRequest) -> InferenceResponse:
    if env.mock_inference:
        # Give placeholder response to speed up development
        return InferenceResponse(response_text="This is a placeholder response")
    response = client.chat.completions.create(
        messages=request.messages,  # type: ignore
        reasoning_effort="none",
        model=env.model,
        max_tokens=env.max_tokens,
        seed=0,
    )
    return InferenceResponse(response_text=response.choices[0].message.content or "")
