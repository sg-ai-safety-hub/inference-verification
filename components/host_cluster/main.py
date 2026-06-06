from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import FastAPI, requests
from fastapi.middleware.cors import CORSMiddleware

from ..lib.signed_envelope import SignedEnvelope
from ..lib.utils import  InferenceRequest, InferenceResponse
from pathlib import Path


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

@app.post("/request")
def request_inference(
    signed_request: SignedEnvelope[InferenceRequest],
) -> SignedEnvelope[InferenceResponse]:
    # Unwrap and verify request
    request = signed_request.unwrap(key=env.host_key).payload

    # Compute response
    print("Received inference request with messages:", request.messages)
    response = run_inference(request)
    print("Inference response:", response.response_text)

    # Sign and return response
    return SignedEnvelope.wrap(
        id=signed_request.data.id, # Match ID
        payload=response,
        key=env.host_key,
    )


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
