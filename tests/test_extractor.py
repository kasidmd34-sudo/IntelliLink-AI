from unittest.mock import MagicMock
import pytest
from app.ai.extractor import InfrastructureExtractor
from app.ai.gemini_client import GeminiClient
from app.schemas.extraction_schema import DocumentExtraction


@pytest.fixture
def mock_gemini_client():
    return MagicMock(spec=GeminiClient)


def test_extractor_successful_parsing(mock_gemini_client):
    mock_payload = {
        "project_name": "NH-48 Corridor Expansion",
        "project_id": "PROJECT_001",
        "report_date": "2026-03-15",
        "contractor_name": "IntelliBuild Infra",
        "activities": [
            {
                "activity_name": "Bituminous Road Work",
                "activity_code": "BOQ-04",
                "work_package": "WP-02",
                "location": "Km 12-18",
                "quantity_completed": 420.0,
                "cumulative_quantity": 4200.0,
                "unit": "m",
                "reported_progress_percent": 70.0,
                "issues": [
                    {
                        "category": "heavy_rainfall",
                        "original_text": "heavy rainfall disrupted bituminous laying",
                        "evidence": "heavy rainfall disrupted bituminous laying",
                        "confidence": 0.98
                    }
                ],
                "observations": ["Compaction meets MORTH specifications"],
                "source_evidence": [
                    {
                        "field_name": "quantity_completed",
                        "extracted_value": "420",
                        "verbatim_text": "420 metres of bituminous road work completed"
                    }
                ]
            }
        ],
        "document_level_issues": [],
        "extraction_status": "SUCCESS"
    }

    mock_gemini_client.generate_structured_extraction.return_value = mock_payload
    extractor = InfrastructureExtractor(client=mock_gemini_client)

    result = extractor.extract(file_path="dummy.pdf", project_id="PROJECT_001")
    assert isinstance(result, DocumentExtraction)
    assert result.extraction_status == "SUCCESS"
    assert len(result.activities) == 1
    assert result.activities[0].activity_name == "Bituminous Road Work"
    assert result.activities[0].quantity_completed == 420.0
    assert result.activities[0].issues[0].category == "heavy_rainfall"


def test_extractor_handles_missing_fields(mock_gemini_client):
    mock_payload = {
        "project_name": None,
        "activities": [
            {
                "activity_name": "Site Clearing",
                "quantity_completed": None,
                "unit": None
            }
        ],
        "extraction_status": "SUCCESS"
    }
    mock_gemini_client.generate_structured_extraction.return_value = mock_payload
    extractor = InfrastructureExtractor(client=mock_gemini_client)

    result = extractor.extract(file_path="dummy.pdf")
    assert result.activities[0].activity_name == "Site Clearing"
    assert result.activities[0].quantity_completed is None
    assert result.activities[0].unit is None


def test_extractor_handles_api_exception(mock_gemini_client):
    mock_gemini_client.generate_structured_extraction.side_effect = RuntimeError("Gemini API rate limit")
    extractor = InfrastructureExtractor(client=mock_gemini_client)

    result = extractor.extract(file_path="corrupt.pdf", project_id="PROJECT_001")
    assert result.extraction_status == "FAILED"
    assert "rate limit" in (result.extraction_notes or "")
    assert len(result.activities) == 0