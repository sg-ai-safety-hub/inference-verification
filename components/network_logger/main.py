from fastapi import Depends, FastAPI, HTTPException
from pydantic_settings import BaseSettings, SettingsConfigDict
import requests

from ..lib.secure_envelope import SecureEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse, check_response, require_key


class Settings(BaseSettings):
    main_cluster_url: str
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
    secure_request: SecureEnvelope[InferenceRequest],
) -> SecureEnvelope[InferenceResponse]:
    # Forward encrypted request to main cluster
    print("Forwarding request:", secure_request.id)
    raw_response = requests.post(
        f"{env.main_cluster_url}/request",
        json=secure_request.model_dump(),
        headers={"Authorization": f"Bearer {env.api_key}"},
    )
    check_response(raw_response)
    response = SecureEnvelope[InferenceResponse].model_validate(raw_response.json())

    # Forward to recomputation cluster for verification
    print("Forwarding response for verification:", response.id)
    raw_response = requests.post(
        f"{env.recomputation_cluster_url}/verify",
        json={
            "secure_request": secure_request.model_dump(),
            "secure_response": response.model_dump(),
        },
        headers={"Authorization": f"Bearer {env.api_key}"},
    )
    check_response(raw_response)

    is_verified = raw_response.json()["verified"]

    # Forward response to gateway if verified else throw error
    if is_verified:
        print("Response verified, forwarding response")
        return response
    else:
        print("Response verification failed")
        raise HTTPException(status_code=400, detail="Recomputation failed")
