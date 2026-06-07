from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ..lib.utils import Message, InferenceRequest, InferenceResponse
from ..lib.signed_envelope import SignedEnvelope
import requests
from pathlib import Path


class Settings(BaseSettings):
    host_key: str
    network_tap_url: str
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

current_id = 0


@app.post("/request")
def request_inference(request: InferenceRequest) -> InferenceResponse:
    global current_id
    current_id += 1
    # Sign request
    signed_request = SignedEnvelope[InferenceRequest].wrap(
        id=current_id, payload=request, key=env.host_key
    )

    # Forward request
    print("Forwarding request:", signed_request.data.payload.messages[-1].content)
    raw_response = requests.post(
        f"{env.network_tap_url}/request", json=signed_request.model_dump()
    )

    # Check for recomputation failure
    if (
        raw_response.status_code == 502
        and raw_response.headers.get("Content-Type") == "application/json"
        and raw_response.json().get("detail") == "Recomputation failed"
    ):
        raise HTTPException(status_code=502, detail="Recomputation failed")
    raw_response.raise_for_status()

    # Else, verify and return response
    response = (
        SignedEnvelope[InferenceResponse]
        .model_validate(raw_response.json())
        .unwrap(key=env.host_key)
    )
    print("Forwarding response:", response.payload.response_text)
    return response.payload
