"""
Generic AES-256-GCM-SIV secure envelope (authenticated encryption)

Schema
-------
{
  "id": int,           // also used as the deterministic nonce counter
  "ciphertext": hex    // AES-256-GCM-SIV(key, nonce=counter(id, direction), payload.model_dump_json())
}

AES-GCM-SIV provides both confidentiality and integrity deterministically.

Usage
-----
To wrap a payload for sending:
    envelope = SecureEnvelope.wrap(id=1, payload=payload, key="key", direction="request")

Decrypt and verify on receipt:
    data = envelope.unwrap(key="key", direction="request")  # raises if key wrong or ciphertext tampered
    payload = data.payload
"""

import hashlib
from typing import Generic, Literal, TypeVar

from cryptography.hazmat.primitives.ciphers.aead import AESGCMSIV
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

# Used to calculate nonce together with ID
Direction = Literal["request", "response"]
_DIRECTION_BYTE = {"request": 0, "response": 1}

class EnvelopeData(BaseModel, Generic[T]):
    id: int
    payload: T


class SecureEnvelope(BaseModel, Generic[T]):
    id: int 
    ciphertext: str

    @staticmethod
    def _derive_key(key: str) -> bytes:
        # Derive a 256-bit key from string
        return hashlib.sha256(key.encode()).digest()

    @staticmethod
    def _nonce(id: int, direction: Direction) -> bytes:
        # Deterministic nonce based on ID and direction
        return bytes([_DIRECTION_BYTE[direction]]) + id.to_bytes(11, "big")

    @classmethod
    def wrap(
        cls, id: int, payload: T, key: str, direction: Direction
    ) -> "SecureEnvelope[T]":
        aead = AESGCMSIV(cls._derive_key(key))
        plaintext = payload.model_dump_json().encode()
        ciphertext = aead.encrypt(
            cls._nonce(id, direction), plaintext, associated_data=None
        )
        return cls(id=id, ciphertext=ciphertext.hex())

    def unwrap(self, key: str, direction: Direction) -> EnvelopeData[T]:
        aead = AESGCMSIV(self._derive_key(key))
        try:
            plaintext = aead.decrypt(
                self._nonce(self.id, direction),
                bytes.fromhex(self.ciphertext),
                associated_data=None,
            )
        except Exception:
            raise Exception("Invalid ciphertext")
        # Convert json to object (InferenceRequest or InferenceResponse)
        (payload_type,) = type(self).__pydantic_generic_metadata__["args"]
        payload = payload_type.model_validate_json(plaintext)
        return EnvelopeData[T](id=self.id, payload=payload)
