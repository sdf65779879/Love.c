import base64
import hashlib

from cryptography.fernet import Fernet

from .config import settings


def cipher():
    key = hashlib.sha256(("LOVE.C:mail:v1:" + settings.secret_key).encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_secret(value: str) -> str:
    return cipher().encrypt(value.encode()).decode() if value else ""


def decrypt_secret(value: str) -> str:
    return cipher().decrypt(value.encode()).decode() if value else ""
