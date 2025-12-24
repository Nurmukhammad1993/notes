from __future__ import annotations

from passlib.context import CryptContext

# Use PBKDF2 to avoid bcrypt backend/version issues and the 72-byte bcrypt limit.
_pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(password: str) -> str:
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return _pwd_context.verify(password, password_hash)
