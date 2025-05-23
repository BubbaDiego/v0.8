import os
import base64
from itertools import cycle

_KEY = os.getenv("WALLET_ENCRYPTION_KEY", "simplekey").encode()


def _xor(data: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, cycle(_KEY)))


def encrypt_key(plain: str | None) -> str | None:
    if plain is None:
        return None
    enc = _xor(plain.encode())
    return base64.b64encode(enc).decode()


def decrypt_key(enc: str | None) -> str | None:
    if enc is None:
        return None
    data = base64.b64decode(enc)
    dec = _xor(data)
    return dec.decode()
