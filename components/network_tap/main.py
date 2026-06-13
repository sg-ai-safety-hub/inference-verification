from fastapi import Depends, FastAPI, HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
import requests

from ..lib.signed_envelope import SignedEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse, check_response, require_key


class Settings(BaseSettings):
    host_cluster_url: str
    recomputation_cluster_url: str
    api_key: str
    model_config = SettingsConfigDict(
        env_file=(".env"),
        dotenv_filtering="only_existing",
    )


env = Settings()  # type: ignore

app = FastAPI(dependencies=[Depends(require_key(env.api_key))])


@app.post("/request")
def request_inference(
    signed_request: SignedEnvelope[InferenceRequest],
) -> SignedEnvelope[InferenceResponse]:
    # Forward request to host cluster
    # More sanitation and bandwidth limiting could be added in the future
    print("Forwarding request:", signed_request.data.payload.messages[-1].content)
    raw_response = requests.post(
        f"{env.host_cluster_url}/request",
        json=signed_request.model_dump(),
        headers={"Authorization": f"Bearer {env.api_key}"},
    )
    check_response(raw_response)
    response = SignedEnvelope[InferenceResponse].model_validate(raw_response.json())

    # Forward to recomputation cluster for verification
    print("Forwarding response for verification:", response.data.payload.response_text)
    raw_response = requests.post(
        f"{env.recomputation_cluster_url}/verify",
        json={
            "signed_request": signed_request.model_dump(),
            "signed_response": response.model_dump(),
        },
        headers={"Authorization": f"Bearer {env.api_key}"},
    )
    check_response(raw_response)

    is_verified = raw_response.json()["verified"]

    # Forward response to gateway if verified else throw error
    if is_verified:
        # More sanitation and bandwidth limiting could be added in the future
        print("Response verified, forwarding response")
        return response
    else:
        print("Response verification failed")
        raise HTTPException(status_code=502, detail="Recomputation failed")
