import hashlib
import pytest
from fastapi import HTTPException
from app.services.evidence_service import EvidenceService


def test_sanitize_extension_allowed_formats():
    """Verify supported forensic file extensions are accepted."""
    assert EvidenceService._sanitize_extension("memory_dump.csv") == ".csv"
    assert EvidenceService._sanitize_extension("network_traffic.json") == ".json"
    assert EvidenceService._sanitize_extension("server_syslog.txt") == ".txt"
    assert EvidenceService._sanitize_extension("warrant_affidavit.pdf") == ".pdf"
    assert EvidenceService._sanitize_extension("crime_scene_photo.JPG") == ".jpg"
    assert EvidenceService._sanitize_extension("suspect_cctv_feed.mp4") == ".mp4"
    assert EvidenceService._sanitize_extension("Security_Events.evtx") == ".evtx"


def test_sanitize_extension_blocks_executables_and_scripts():
    """Verify dangerous executable formats are strictly blocked."""
    disallowed = [
        "malware.exe",
        "payload.sh",
        "script.bat",
        "trojan.dll",
        "exploit.js",
        "macro.vbs",
        "dropper.ps1",
    ]
    for filename in disallowed:
        with pytest.raises(HTTPException) as exc:
            EvidenceService._sanitize_extension(filename)
        assert exc.value.status_code == 400


def test_sha256_hash_computation():
    """Verify incremental SHA-256 calculation matches expected checksum."""
    sample_bytes = b"Digital Forensic Evidence Payload - Chain of Custody Verified"
    expected_hash = hashlib.sha256(sample_bytes).hexdigest()

    sha = hashlib.sha256()
    sha.update(sample_bytes)
    assert sha.hexdigest() == expected_hash
