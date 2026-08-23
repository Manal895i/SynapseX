import pytest
from app.security.password import hash_password, verify_password
from app.security.jwt import create_access_token, decode_access_token


def test_password_hashing():
    """Verify that bcrypt hashes passwords and matches correctly."""
    pwd = "SecureInvestigatorPassword99"
    hashed = hash_password(pwd)
    assert hashed != pwd
    assert verify_password(pwd, hashed) is True
    assert verify_password("WrongPassword123", hashed) is False


def test_jwt_token_generation_and_decoding():
    """Verify JWT access token creation and claim recovery."""
    user_id = 42
    claims = {"role": "investigator", "email": "officer@adeip.internal"}
    token = create_access_token(subject=user_id, extra_claims=claims)
    assert isinstance(token, str)

    payload = decode_access_token(token)
    assert payload is not None
    assert payload.get("sub") == str(user_id)
    assert payload.get("role") == "investigator"
    assert payload.get("email") == "officer@adeip.internal"
    assert "exp" in payload


def test_invalid_jwt_decoding():
    """Verify corrupted or invalid token returns None."""
    payload = decode_access_token("invalid.jwt.token")
    assert payload is None
