import pytest

from src.domain.services.auth import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class TestPasswordHashing:
    def test_hash_is_not_plaintext(self):
        assert hash_password("secret") != "secret"

    def test_verify_correct_password(self):
        hashed = hash_password("secret")
        assert verify_password("secret", hashed) is True

    def test_reject_wrong_password(self):
        hashed = hash_password("secret")
        assert verify_password("wrong", hashed) is False

    def test_same_password_produces_different_hashes(self):
        # bcrypt uses a random salt per hash
        assert hash_password("secret") != hash_password("secret")


class TestJWT:
    def test_encode_decode_roundtrip(self):
        token = create_access_token(subject="user-123")
        payload = decode_access_token(token)
        assert payload["sub"] == "user-123"

    def test_token_contains_expiry(self):
        token = create_access_token(subject="user-123")
        payload = decode_access_token(token)
        assert "exp" in payload

    def test_tampered_token_is_rejected(self):
        token = create_access_token(subject="user-123")
        tampered = token[:-4] + "XXXX"
        with pytest.raises(ValueError, match="invalid"):
            decode_access_token(tampered)

    def test_extra_claims_are_preserved(self):
        token = create_access_token(subject="user-123", extra={"role": "admin"})
        payload = decode_access_token(token)
        assert payload["role"] == "admin"
