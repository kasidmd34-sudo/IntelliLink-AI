import importlib
import json
import logging
from typing import Any, Dict, Optional
from app.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class GeminiClient:
    """Lazy wrapper around the official Google GenAI SDK.

    Lazy imports allow the offline heuristic/test pipeline to work even when the
    Gemini SDK is not installed or the API key is intentionally absent.
    """
    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model_name = model_name or settings.GEMINI_MODEL
        self.client = None
        self.types = None
        if self.api_key:
            self._initialize()

    def _initialize(self) -> None:
        try:
            genai = importlib.import_module("google.genai")
            self.types = importlib.import_module("google.genai.types")
            self.client = genai.Client(api_key=self.api_key)
        except Exception as exc:
            logger.warning("Gemini SDK unavailable; heuristic fallback remains available: %s", exc)
            self.client = None

    def _require_client(self) -> None:
        if not self.client:
            raise RuntimeError("Gemini client is unavailable. Install google-genai and set GEMINI_API_KEY.")

    def generate_structured_extraction(self, prompt: str, file_path: Optional[str] = None, mime_type: Optional[str] = None) -> Dict[str, Any]:
        self._require_client()
        contents = []
        if file_path:
            with open(file_path, "rb") as f:
                data = f.read()
            mime_type = mime_type or ("application/pdf" if file_path.lower().endswith(".pdf") else "image/jpeg")
            contents.append(self.types.Part.from_bytes(data=data, mime_type=mime_type))
        contents.append(prompt)
        response = self.client.models.generate_content(
            model=self.model_name, contents=contents,
            config=self.types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
        )
        if not getattr(response, "text", None):
            raise ValueError("Empty response received from Gemini API.")
        return json.loads(response.text)

    def generate_text_extraction(self, prompt: str, text_content: str) -> Dict[str, Any]:
        self._require_client()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=[f"Input Document Text Content:\n```\n{text_content}\n```", prompt],
            config=self.types.GenerateContentConfig(response_mime_type="application/json", temperature=0.1)
        )
        if not getattr(response, "text", None):
            raise ValueError("Empty response received from Gemini API.")
        return json.loads(response.text)
