from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

from fastapi import HTTPException, UploadFile

MAX_UPLOAD_BYTES = 100 * 1024 * 1024  # 100 MB per file
_CHUNK_SIZE = 1024 * 1024


def safe_filename(filename: str | None, fallback: str = "upload") -> str:
    """Return a filesystem-safe filename while keeping the original extension."""
    name = Path(filename or fallback).name.strip() or fallback
    name = re.sub(r"[^A-Za-z0-9._-]+", "_", name)
    return name[:180]


def require_extension(filename: str | None, allowed_extensions: Iterable[str]) -> str:
    ext = Path(filename or "").suffix.lower()
    allowed = {item.lower() for item in allowed_extensions}
    if ext not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '{ext or 'unknown'}'. Allowed: {', '.join(sorted(allowed))}",
        )
    return ext


async def save_upload_file(
    upload: UploadFile,
    destination_dir: Path,
    allowed_extensions: Iterable[str],
    *,
    max_bytes: int = MAX_UPLOAD_BYTES,
) -> Path:
    """Validate and save an uploaded file to destination_dir."""
    require_extension(upload.filename, allowed_extensions)
    destination_dir.mkdir(parents=True, exist_ok=True)

    output_path = destination_dir / safe_filename(upload.filename)
    total = 0

    with output_path.open("wb") as out:
        while True:
            chunk = await upload.read(_CHUNK_SIZE)
            if not chunk:
                break
            total += len(chunk)
            if total > max_bytes:
                raise HTTPException(status_code=413, detail="File is too large. Maximum allowed size is 100 MB.")
            out.write(chunk)

    if total == 0:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    return output_path
