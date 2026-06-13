import secrets
from typing import Literal
from fastapi import Header, HTTPException
from pydantic import BaseModel
import requests


# Check for bearer token
def require_key(api_key: str):
    def dependency(authorization: str = Header("")):
        if not api_key: # Auth disabled
            return
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer" or not secrets.compare_digest(token, api_key):
            raise HTTPException(status_code=401, detail="Invalid API key")

    return dependency


class Message(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: str


class InferenceRequest(BaseModel):
    messages: list[Message]


class InferenceResponse(BaseModel):
    response_text: str


# Catch errors from upstream servers
def check_response(response: requests.Response) -> None:
    try:
        response.raise_for_status()
    except Exception as e:
        print("Error forwarding request:", e)
        raise HTTPException(status_code=502, detail="Error forwarding request")
