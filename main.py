from typing import Literal

from openai import OpenAI
from pydantic import BaseModel
from pydantic_settings import BaseSettings, SettingsConfigDict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


class Settings(BaseSettings):
    inference_url: str
    max_tokens: int
    model: str
    model_config = SettingsConfigDict(env_file=".env")
    mock_inference: bool = False

settings = Settings()  # type: ignore
client = OpenAI(base_url=settings.inference_url, api_key="unused")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class Message(BaseModel):
    role: Literal["user", "system", "assistant"]
    content: str


class InferenceRequest(BaseModel):
    messages: list[Message]


class InferenceResponse(BaseModel):
    response_text: str


@app.post("/request")
def request_inference(body: InferenceRequest) -> InferenceResponse:
    messages = body.model_dump()["messages"]
    print("Received inference request with messages:", messages)
    response = run_inference(messages)
    print("Inference response:", response)
    return InferenceResponse(response_text=response)


def run_inference(messages: list[Message]) -> str:
    if settings.mock_inference:
        # Give placeholder response to speed up development
        return "This is a placeholder response"
    response = client.chat.completions.create(
        messages=messages,  # type: ignore
        reasoning_effort="none",
        model=settings.model,
        max_tokens=settings.max_tokens,
        seed=0,
    )
    return response.choices[0].message.content or ""
