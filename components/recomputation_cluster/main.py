from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import socketio

from ..lib.inference import run_inference
from ..lib.signed_envelope import SignedEnvelope
from ..lib.utils import InferenceRequest, InferenceResponse


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
sio = socketio.AsyncServer(
    async_mode="asgi",
    cors_allowed_origins=[],  # Handled by FastAPI
)
app.mount("/socket.io", socketio.ASGIApp(sio, socketio_path=""))


state = {
    "status": "Ready",
    "request": None,
    "received_response": None,
    "recomputed_response": None,
    "verified": None,
}


@sio.event
async def connect(sid, environ, auth):
    # Send state on connect
    await sio.emit("state", state, to=sid)


@app.post("/verify")
async def verify_inference(
    signed_request: SignedEnvelope[InferenceRequest],
    signed_response: SignedEnvelope[InferenceResponse],
):
    # Unwrap request and response
    request = signed_request.data.payload
    response = signed_response.data.payload

    # Broadcast the received request and response
    state["status"] = "Running"
    state["request"] = request.messages[-1].content
    state["received_response"] = response.response_text
    state["recomputed_response"] = None
    state["verified"] = None
    await sio.emit("state", state)

    # Recompute response
    print(f"Running recomputation for message: {request.messages[-1].content}")
    recomputed = await run_inference(request, on_chunk=log_chunk)

    # Compare responses
    print(f"Received response:   {response.response_text}")
    print(f"Recomputed response: {recomputed.response_text}")
    verified = recomputed.response_text == response.response_text
    print(f"Verification {"successful" if verified else "failed"}")

    # Broadcast the recomputed response and verification result
    state["status"] = "Done"
    state["recomputed_response"] = recomputed.response_text
    state["verified"] = verified
    await sio.emit("state", state)

    return {"verified": verified}


@app.post("/clear")
async def clear():
    # Reset to ready
    state["status"] = "Ready"
    state["request"] = None
    state["received_response"] = None
    state["recomputed_response"] = None
    state["verified"] = None
    await sio.emit("state", state)


# Stream results to dashboard
async def log_chunk(chunk: str):
    state["recomputed_response"] = (state["recomputed_response"] or "") + chunk
    await sio.emit("state", state)
