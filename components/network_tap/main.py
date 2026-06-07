from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from ..lib.utils import Message, InferenceRequest, InferenceResponse
from ..lib.signed_envelope import SignedEnvelope
import requests
from pathlib import Path


class Settings(BaseSettings):
    host_cluster_url: str
    recomputation_cluster_url: str
    model_config = SettingsConfigDict(
        env_file=(".env"),
        dotenv_filtering="only_existing",
    )


env = Settings()  # type: ignore

app = FastAPI()


@app.post("/request")
def request_inference(
    signed_request: SignedEnvelope[InferenceRequest],
) -> SignedEnvelope[InferenceResponse]:
    # Forward request to host cluster
    # More sanitation and bandwidth limiting could be added in the future
    print("Forwarding request:", signed_request.data.payload.messages[-1].content)
    raw_response = requests.post(
        f"{env.host_cluster_url}/request", json=signed_request.model_dump()
    )
    raw_response.raise_for_status()
    response = SignedEnvelope[InferenceResponse].model_validate(raw_response.json())

    # Forward to recomputation cluster for verification
    print("Forwarding response for verification:", response.data.payload.response_text)
    raw_response = requests.post(
        f"{env.recomputation_cluster_url}/verify",
        json={
            "signed_request": signed_request.model_dump(),
            "signed_response": response.model_dump(),
        },
    )
    raw_response.raise_for_status()
    is_verified = raw_response.json()["verified"]

    # Forward response to gateway if verified else throw error
    if is_verified:
        # More sanitation and bandwidth limiting could be added in the future
        print("Response verified, forwarding response")
        return response
    else:
        print("Response verification failed")
        raise HTTPException(status_code=502, detail="Recomputation failed")
