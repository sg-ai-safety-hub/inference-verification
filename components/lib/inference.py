import random
from typing import Callable
import asyncio
from openai import OpenAI
from pydantic_settings import BaseSettings, SettingsConfigDict
from .utils import InferenceRequest, InferenceResponse, Message


class InferenceSettings(BaseSettings):
    inference_url: str
    max_tokens: int
    model: str
    mock_inference: bool = False
    model_config = SettingsConfigDict(
        env_file=(".env"),
        dotenv_filtering="only_existing",
    )


env = InferenceSettings()  # type: ignore
client = OpenAI(base_url=env.inference_url, api_key="unused")


async def run_inference(
    request: InferenceRequest,
    *,
    on_chunk: Callable[[str], None],  # Streaming callback\
    # Simulate covert training by replacing output with random hex characters
    simulate_training: Callable[[], bool] = lambda: False,
) -> InferenceResponse:
    response_text = ""

    async def handle_chunk(chunk: str):
        if simulate_training():
            chunk = "".join(random.choices("0123456789ABCDEF", k=len(chunk)))
        nonlocal response_text
        response_text += chunk
        await on_chunk(chunk)

    if env.mock_inference:
        # Give placeholder response if LLM is not available
        for word in "This is a placeholder response".split():
            await handle_chunk(word + " ")
            await asyncio.sleep(0.15)
    else:
        # Prepend user message as model requires conversations to start with user
        messages = [Message(role="user", content="Hi"), *request.messages]
        response = client.chat.completions.create(
            messages=messages,  # type: ignore
            reasoning_effort="none",
            model=env.model,
            max_tokens=env.max_tokens,
            seed=0,
            stream=True,
        )
        for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                await handle_chunk(content)

    return InferenceResponse(response_text=response_text)
