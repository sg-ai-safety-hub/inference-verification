from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings, SettingsConfigDict
import requests

from ..lib.signed_envelope import SignedEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse, check_response, require_key


class Settings(BaseSettings):
    host_key: str
    network_tap_url: str
    api_key: str
    model_config = SettingsConfigDict(
        env_file=(".env", Path(__file__).parent / ".env"),
        dotenv_filtering="only_existing",
    )


env = Settings()  # type: ignore

app = FastAPI(dependencies=[Depends(require_key(env.api_key))])
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
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
        f"{env.network_tap_url}/request",
        json=signed_request.model_dump(),
        headers={"Authorization": f"Bearer {env.api_key}"},
    )

    # Check for recomputation failure
    if (
        raw_response.status_code == 400
        and raw_response.headers.get("Content-Type") == "application/json"
        and raw_response.json().get("detail") == "Recomputation failed"
    ):
        raise HTTPException(status_code=400, detail="Recomputation failed")
    check_response(raw_response)

    # Else, verify and return response
    response = (
        SignedEnvelope[InferenceResponse]
        .model_validate(raw_response.json())
        .unwrap(key=env.host_key)
    )
    print("Forwarding response:", response.payload.response_text)
    return response.payload
