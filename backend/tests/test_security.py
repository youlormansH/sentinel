import pytest

from app.core.security import (
    create_token,
    decode_token,
    decrypt_value,
    encrypt_value,
    hash_password,
    verify_password,
)


def test_password_hash_is_not_plaintext():
    hashed = hash_password("SuperSecret123!")
    assert hashed != "SuperSecret123!"
    assert hashed.startswith("$argon2")


def test_password_verify_roundtrip():
    hashed = hash_password("SuperSecret123!")
    assert verify_password("SuperSecret123!", hashed) is True
    assert verify_password("WrongPassword1!", hashed) is False


def test_access_token_roundtrip():
    token, expire, jti = create_token("user-123", "access")
    payload = decode_token(token)
    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert payload["jti"] == jti


def test_refresh_token_has_longer_expiry_than_access():
    _, access_expire, _ = create_token("user-123", "access")
    _, refresh_expire, _ = create_token("user-123", "refresh")
    assert refresh_expire > access_expire


def test_decode_rejects_tampered_token():
    token, _, _ = create_token("user-123", "access")
    tampered = token[:-2] + ("aa" if token[-2:] != "aa" else "bb")
    with pytest.raises(ValueError):
        decode_token(tampered)


def test_aes_encryption_roundtrip():
    secret = "JBSWY3DPEHPK3PXP"
    encrypted = encrypt_value(secret)
    assert encrypted != secret
    assert decrypt_value(encrypted) == secret
