"""
File Security and Path Traversal Prevention Utilities for ADEIP.

Requirements:
- Strict path traversal validation (prevents ../ and absolute path escape).
- Sanitizes incoming filenames.
- Enforces strict allowed vs. blocked extension rules and double-extension detection.
"""
import os
import re
from typing import List, Optional
from fastapi import HTTPException, status

from app.core.config import settings


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes user-provided filename by removing path separators, null bytes,
    and control characters while preserving a clean basename.
    """
    if not filename:
        return "unnamed_evidence"

    # Extract basename only
    base = os.path.basename(filename.replace("\\", "/"))

    # Remove null bytes and control chars
    base = re.sub(r"[\x00-\x1f\x7f]", "", base)

    # Strip dangerous characters
    base = re.sub(r'[\<\>\:\"\/\\\|\?\*]', "_", base)

    # Strip leading/trailing spaces and dots
    base = base.strip(". ")

    if not base:
        return "unnamed_evidence"

    return base


def safe_join_path(base_dir: str, *subpaths: str) -> str:
    """
    Safely joins a base directory with one or more subpaths.
    Strictly verifies that the resolved path is inside the canonical base directory,
    preventing path traversal attacks (e.g., ../../../etc/passwd).
    """
    canonical_base = os.path.abspath(base_dir)
    target_path = os.path.abspath(os.path.join(canonical_base, *subpaths))

    try:
        common = os.path.commonpath([canonical_base, target_path])
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file path structure.",
        )

    if common != canonical_base:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Security error: Path traversal outside designated storage directory is prohibited.",
        )

    return target_path


def validate_file_safety(
    filename: str,
    allowed_extensions: Optional[List[str]] = None,
    blocked_extensions: Optional[List[str]] = None,
):
    """
    Validates file extension safety, blocking dangerous scripts/binaries
    and double-extension evasion techniques.
    """
    allowed = allowed_extensions or settings.ALLOWED_EVIDENCE_EXTENSIONS
    blocked = blocked_extensions or settings.BLOCKED_EXTENSIONS

    lower_name = filename.lower()
    _, ext = os.path.splitext(lower_name)

    # Check blocked extensions
    if ext in blocked:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File extension '{ext}' is explicitly prohibited for security.",
        )

    # Check allowed extensions
    if ext not in allowed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file extension '{ext}'. Allowed extensions: {', '.join(allowed)}",
        )

    # Check for dangerous double extensions (e.g. evidence.php.csv or exploit.exe.json)
    parts = lower_name.split(".")
    if len(parts) > 2:
        inner_extensions = [f".{p}" for p in parts[1:-1]]
        for inner_ext in inner_extensions:
            if inner_ext in blocked:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Security error: Dangerous nested extension '{inner_ext}' detected in filename.",
                )
