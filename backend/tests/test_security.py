from datetime import timedelta
import pytest
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    get_password_hash,
    verify_password,
)


def test_password_hashing():
    password = "MySecurePassword123!"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword!", hashed) is False


def test_jwt_access_token_creation_and_decoding():
    payload = {"sub": "12345678-1234-5678-1234-567812345678", "role": "EMPLOYEE", "region": "India"}
    token = create_access_token(payload, expires_delta=timedelta(minutes=15))

    decoded = decode_token(token)
    assert decoded["sub"] == "12345678-1234-5678-1234-567812345678"
    assert decoded["role"] == "EMPLOYEE"
    assert decoded["region"] == "India"
    assert decoded["type"] == "access"
    assert "exp" in decoded


def test_jwt_refresh_token_creation_and_decoding():
    payload = {"sub": "user_abc"}
    token = create_refresh_token(payload)

    decoded = decode_token(token)
    assert decoded["sub"] == "user_abc"
    assert decoded["type"] == "refresh"


def test_invalid_token_decoding_raises_error():
    with pytest.raises(ValueError):
        decode_token("this.is.not.a.valid.jwt")
