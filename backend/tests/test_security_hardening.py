"""
Security Hardening Unit Tests for ADEIP Backend.
"""
import pytest
from fastapi import HTTPException
from app.core.file_security import (
    safe_join_path,
    sanitize_filename,
    validate_file_safety,
)
from app.core.rate_limit import InMemoryRateLimiter


@pytest.mark.asyncio
async def test_rate_limiter_allows_under_limit_and_blocks_over_limit():
    """Verify rate limiter allows requests up to limit and blocks subsequent with 429."""
    limiter = InMemoryRateLimiter()
    test_key = "127.0.0.1:auth_test"

    # Limit = 3 requests per 60s
    res1 = await limiter.check_rate_limit(key=test_key, limit=3, window_seconds=60)
    assert res1["remaining"] == 2

    res2 = await limiter.check_rate_limit(key=test_key, limit=3, window_seconds=60)
    assert res2["remaining"] == 1

    res3 = await limiter.check_rate_limit(key=test_key, limit=3, window_seconds=60)
    assert res3["remaining"] == 0

    # 4th request must trigger 429 HTTPException
    with pytest.raises(HTTPException) as exc_info:
        await limiter.check_rate_limit(key=test_key, limit=3, window_seconds=60)

    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
    assert "Retry-After" in exc_info.value.headers


def test_sanitize_filename_prevents_directory_traversal():
    """Verify filename sanitizer strips path traversal sequences, null bytes, and dangerous characters."""
    assert sanitize_filename("../../../etc/passwd") == "passwd"
    assert sanitize_filename("..\\..\\windows\\system32\\cmd.exe") == "cmd.exe"
    assert sanitize_filename("safe_evidence.csv\x00.exe") == "safe_evidence.csv.exe"
    assert sanitize_filename("test:file*name?.json") == "test_file_name_.json"


def test_safe_join_path_prevents_escape():
    """Verify safe_join_path raises HTTPException(400) on path traversal attempts."""
    base_dir = "storage/evidence_vault"

    # Valid subpath
    valid_path = safe_join_path(base_dir, "case_1", "evidence_101.csv")
    assert "case_1" in valid_path

    # Path traversal attack attempting to escape base dir
    with pytest.raises(HTTPException) as exc_info:
        safe_join_path(base_dir, "..", "..", "etc", "shadow")

    assert exc_info.value.status_code == 400
    assert "Path traversal" in exc_info.value.detail


def test_validate_file_safety_blocks_prohibited_and_nested_extensions():
    """Verify blocked executable extensions and double-extension evasion attacks are rejected."""
    # Prohibited executable
    with pytest.raises(HTTPException) as exc_info:
        validate_file_safety("malware.exe")
    assert exc_info.value.status_code == 400

    # Dangerous script
    with pytest.raises(HTTPException) as exc_info:
        validate_file_safety("exploit.php")
    assert exc_info.value.status_code == 400

    # Double extension evasion (e.g., shell.php.csv)
    with pytest.raises(HTTPException) as exc_info:
        validate_file_safety("payload.exe.csv")
    assert exc_info.value.status_code == 400
    assert "Dangerous nested extension" in exc_info.value.detail

    # Valid forensic files should pass without exception
    validate_file_safety("network_capture.csv")
    validate_file_safety("system_security.evtx")
    validate_file_safety("host_telemetry.json")
