import time
import uuid
from pathlib import Path
from typing import Any, Dict, Optional
# pyrefly: ignore [missing-import]
import pymupdf as fitz  # PyMuPDF
from app.config.settings import get_settings
from app.utils.file_utils import detect_file_type

settings = get_settings()


class DocumentProcessor:
    """Handles file ingestion, size checks, and PyMuPDF text preprocessing."""

    def __init__(self, upload_dir: Optional[Path] = None):
        self.upload_dir = upload_dir or settings.UPLOAD_DIR
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    async def save_and_validate(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        file_type, is_supported = detect_file_type(filename, content_type)
        if not is_supported:
            raise ValueError(f"Unsupported file format '{file_type}'. IntelliLink supports PDF, PNG, JPG, and JPEG.")

        size_mb = len(file_bytes) / (1024 * 1024)
        if size_mb > settings.MAX_UPLOAD_SIZE_MB:
            raise ValueError(f"File size ({size_mb:.2f} MB) exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB.")

        doc_id = f"doc_{uuid.uuid4().hex[:12]}"
        saved_filename = f"{doc_id}_{filename}"
        file_path = self.upload_dir / saved_filename

        with open(file_path, "wb") as f:
            f.write(file_bytes)

        metadata = {
            "document_id": doc_id,
            "filename": filename,
            "file_type": file_type,
            "file_path": str(file_path),
            "file_size_bytes": len(file_bytes),
            "project_id": project_id,
            "upload_timestamp": time.time(),
            "is_scanned": False,
            "page_count": 1
        }

        if file_type == "pdf":
            try:
                doc = fitz.open(file_path)
                metadata["page_count"] = len(doc)
                total_text_len = sum(len(page.get_text()) for page in doc)
                if len(doc) > 0 and (total_text_len / len(doc)) < 30:
                    metadata["is_scanned"] = True
                doc.close()
            except Exception as e:
                metadata["pdf_parse_warning"] = str(e)

        return metadata

    def extract_text_fallback(self, file_path: str) -> str:
        path = Path(file_path)
        if path.suffix.lower() == ".pdf":
            text = ""
            doc = fitz.open(path)
            for page_num in range(len(doc)):
                page = doc[page_num]
                text += f"\n--- Page {page_num + 1} ---\n" + page.get_text()
            doc.close()
            return text
        return ""