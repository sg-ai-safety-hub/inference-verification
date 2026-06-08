from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import Body, FastAPI, requests
from fastapi.middleware.cors import CORSMiddleware
import socketio

from ..lib.signed_envelope import SignedEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse
from pathlib import Path
import random


class Settings(BaseSettings):
    inference_url: str
    max_tokens: int
    model: str
    mock_inference: bool = False
    host_key: str
    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).parent / ".env"),
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
    response = run(request)
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


def run(request: InferenceRequest) -> InferenceResponse:
    if state["is_training"]:
        response_text = "".join(random.choices("0123456789abcdef", k=32))
    elif env.mock_inference:
        # Give placeholder response to speed up development
        response_text = "This is a placeholder response"
    else:
        response = client.chat.completions.create(
            messages=request.messages,  # type: ignore
            reasoning_effort="none",
            model=env.model,
            max_tokens=env.max_tokens,
            seed=0,
        )
        response_text = response.choices[0].message.content or ""
    return InferenceResponse(response_text=response_text)


@app.post("/set-training")
async def set_training(new: bool = Body()):
    state["is_training"] = new
    await sio.emit("state", state)
