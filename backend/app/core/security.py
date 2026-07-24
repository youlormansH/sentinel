import base64
import hashlib
import os
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
from uuid import UUID

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from jose import JWTError, jwt

from app.core.config import settings

_ph = PasswordHasher(time_cost=3, memory_cost=65536, parallelism=4)


# ---------------------------------------------------------------------------
# Password hashing (Argon2id)
# ---------------------------------------------------------------------------
def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return _ph.verify(password_hash, password)
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def needs_rehash(password_hash: str) -> bool:
    return _ph.check_needs_rehash(password_hash)


# ---------------------------------------------------------------------------
# JWT access / refresh tokens
# ---------------------------------------------------------------------------
TokenType = Literal["access", "refresh"]


def create_token(subject: str | UUID, token_type: TokenType, extra_claims: dict[str, Any] | None = None) -> tuple[str, datetime, str]:
    now = datetime.now(timezone.utc)
    if token_type == "access":
        expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    else:
        expires_delta = timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    expire = now + expires_delta
    jti = secrets.token_urlsafe(16)
    to_encode: dict[str, Any] = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": expire,
        "jti": jti,
    }
    if extra_claims:
        to_encode.update(extra_claims)
    encoded = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded, expire, jti


def decode_token(token: str) -> dict[str, Any]:
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError as exc:
        raise ValueError("Invalid or expired token") from exc


# ---------------------------------------------------------------------------
# AES-256-GCM encryption for sensitive fields (e.g. TOTP secrets)
# ---------------------------------------------------------------------------
def _aes_key() -> bytes:
    raw = settings.AES_ENCRYPTION_KEY.encode("utf-8")
    # Normalize any provided secret into a stable 32-byte key.
    return hashlib.sha256(raw).digest()


def encrypt_value(plaintext: str) -> str:
    key = _aes_key()
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, plaintext.encode("utf-8"), None)
    return base64.urlsafe_b64encode(nonce + ciphertext).decode("utf-8")


def decrypt_value(token: str) -> str:
    key = _aes_key()
    aesgcm = AESGCM(key)
    raw = base64.urlsafe_b64decode(token.encode("utf-8"))
    nonce, ciphertext = raw[:12], raw[12:]
    return aesgcm.decrypt(nonce, ciphertext, None).decode("utf-8")


def generate_secure_token(n_bytes: int = 32) -> str:
    return secrets.token_urlsafe(n_bytes)


def hash_token(token: str) -> str:
    """One-way hash for storing opaque tokens (refresh/reset/verify) at rest."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
