from typing import Literal
from fastapi import HTTPException
from pydantic import BaseModel
import requests


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
