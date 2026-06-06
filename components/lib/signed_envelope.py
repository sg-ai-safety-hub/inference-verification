"""
Generic HMAC-SHA256 signed envelope

Schema
-------
{
  "data": {
    "id": int,
    "payload": InferenceRequest/InferenceResponse
  },
  "signature": hex   // HMAC-SHA256(key, data.model_dump_json())
}

Usage
-----
To wrap a payload for sending:
    envelope = SignedEnvelope.wrap(id=1, payload=payload, key="key")

Verify and unwrap on receipt:
    payload = envelope.unwrap(key="key")  # raises if signature invalid
"""

from pydantic import BaseModel
import hashlib
import hmac
from typing import Generic, TypeVar

T = TypeVar("T")


class EnvelopeData(BaseModel, Generic[T]):
    id: int
    payload: T


class SignedEnvelope(BaseModel, Generic[T]):
    data: EnvelopeData[T]
    signature: str  # hex HMAC-SHA256 over data.model_dump_json()

    @classmethod
    def _sign(cls, data: EnvelopeData[T], key: str) -> str:
        return hmac.new(
            key.encode(), data.model_dump_json().encode(), hashlib.sha256
        ).hexdigest()

    @classmethod
    def wrap(cls, id: int, payload: T, key: str) -> "SignedEnvelope[T]":
        data = EnvelopeData(id=id, payload=payload)
        return cls(data=data, signature=cls._sign(data, key))

    def unwrap(self, key: str) -> EnvelopeData[T]:
        if not hmac.compare_digest(self._sign(self.data, key), self.signature):
            raise Exception(f"Invalid signature")
        return self.data
