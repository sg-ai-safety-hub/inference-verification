from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import FastAPI, requests
from fastapi.middleware.cors import CORSMiddleware

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


@app.post("/verify")
def verify_inference(
    signed_request: SignedEnvelope[InferenceRequest],
    signed_response: SignedEnvelope[InferenceResponse],
):
    # Unwrap request and response
    request = signed_request.data.payload
    response = signed_response.data.payload

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
