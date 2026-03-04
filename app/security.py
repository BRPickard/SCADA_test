import base64
import hashlib
from passlib.context import CryptContext
from app.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return pwd_context.verify(password, hashed)


def encrypt_secret(value: str) -> str:
    key = get_settings().master_key.encode()
    digest = hashlib.sha256(key).digest()
    data = value.encode()
    out = bytes([b ^ digest[i % len(digest)] for i, b in enumerate(data)])
    return base64.urlsafe_b64encode(out).decode()


def decrypt_secret(value: str) -> str:
    key = get_settings().master_key.encode()
    digest = hashlib.sha256(key).digest()
    data = base64.urlsafe_b64decode(value.encode())
    out = bytes([b ^ digest[i % len(digest)] for i, b in enumerate(data)])
    return out.decode()
