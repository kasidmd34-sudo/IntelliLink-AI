import mimetypes
from pathlib import Path
from typing import Tuple


def detect_file_type(filename: str, content_type: str | None = None) -> Tuple[str, bool]:
    """Determines normalized file extension and checks support for PDF, PNG, JPG, and JPEG."""
    ext = Path(filename).suffix.lower().lstrip(".")
    if ext in ["pdf"]:
        return "pdf", True
    if ext in ["png", "jpg", "jpeg"]:
        return ext, True

    if content_type:
        guessed_ext = mimetypes.guess_extension(content_type)
        if guessed_ext:
            norm_ext = guessed_ext.lower().lstrip(".")
            if norm_ext in ["pdf", "png", "jpg", "jpeg"]:
                return norm_ext, True

    return ext or "unknown", False