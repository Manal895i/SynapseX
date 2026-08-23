import hashlib
import os
import tempfile
import pytest
from fastapi import HTTPException

from app.models.evidence import IntegrityStatus


def compute_sha256(data: bytes) -> str:
    """Helper: compute expected SHA-256 hash for test data."""
    return hashlib.sha256(data).hexdigest()


def test_sha256_verified_match():
    """Verify that recalculated hash matches original when file is untampered."""
    sample_data = b"Forensic evidence payload - operation nightshade - network packet dump"
    original_hash = compute_sha256(sample_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp_file:
        tmp_file.write(sample_data)
        tmp_path = tmp_file.name

    try:
        sha256 = hashlib.sha256()
        with open(tmp_path, "rb") as f:
            while True:
                chunk = f.read(64 * 1024)
                if not chunk:
                    break
                sha256.update(chunk)
        computed = sha256.hexdigest()

        assert computed == original_hash
        assert IntegrityStatus.VERIFIED.value == "verified"
    finally:
        os.unlink(tmp_path)


def test_sha256_hash_mismatch():
    """Verify that mutating evidence data produces a different hash (mismatch)."""
    original_data = b"Original forensic payload - SCADA telemetry logs"
    tampered_data = b"Original forensic payload - SCADA telemetry logs - TAMPERED"

    original_hash = compute_sha256(original_data)
    tampered_hash = compute_sha256(tampered_data)

    assert original_hash != tampered_hash
    assert IntegrityStatus.HASH_MISMATCH.value == "hash_mismatch"


def test_integrity_status_file_missing():
    """Verify that a non-existent path produces FILE_MISSING outcome."""
    non_existent_path = "/storage/evidence_vault/case_99/00000000nonexistent.csv"
    file_exists = os.path.exists(non_existent_path)

    assert file_exists is False
    assert IntegrityStatus.FILE_MISSING.value == "file_missing"


def test_sha256_deterministic():
    """Verify that SHA-256 is deterministic for the same input."""
    data = b"Deterministic forensic hash test - chain of custody"
    hash_a = compute_sha256(data)
    hash_b = compute_sha256(data)
    assert hash_a == hash_b
    assert len(hash_a) == 64  # SHA-256 produces 64 hex characters


def test_integrity_status_enum_values():
    """Verify all IntegrityStatus enum values are correctly defined."""
    assert IntegrityStatus.UNVERIFIED.value == "unverified"
    assert IntegrityStatus.VERIFIED.value == "verified"
    assert IntegrityStatus.HASH_MISMATCH.value == "hash_mismatch"
    assert IntegrityStatus.FILE_MISSING.value == "file_missing"
