from typing import Literal
from pydantic import BaseModel

class Message(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: str

class InferenceRequest(BaseModel):
    messages: list[Message]


class InferenceResponse(BaseModel):
    response_text: str

