from typing import Optional
from app.config.settings import get_settings
from app.schemas.extraction_schema import ExtractedActivity
from app.schemas.matching_schema import MatchCandidate
from app.schemas.response_schema import ConfidenceBreakdown, ValidationReport
settings = get_settings()

class ConfidenceScorer:
    """Separates extraction quality from match quality to avoid double-counting signals."""
    @classmethod
    def calculate(cls, activity: ExtractedActivity, validation: ValidationReport, best_match: Optional[MatchCandidate]) -> ConfidenceBreakdown:
        extraction_quality = (
            (1.0 if activity.activity_name else 0.0) * 0.35 +
            (1.0 if activity.quantity_completed is not None else 0.0) * 0.25 +
            (1.0 if activity.unit else 0.0) * 0.15 +
            (1.0 if activity.location else 0.5) * 0.10 +
            (1.0 if activity.source_evidence else 0.0) * 0.15
        )
        validation_score = 1.0 if validation.is_valid else 0.0
        validation_score = max(0.0, validation_score - 0.05 * len(validation.warnings))
        match_score = best_match.score if best_match else 0.0
        overall = round(min(1.0, max(0.0, extraction_quality * 0.35 + validation_score * 0.20 + match_score * 0.45)), 4)
        level = "HIGH" if overall >= settings.CONFIDENCE_HIGH_THRESHOLD else "MEDIUM" if overall >= settings.CONFIDENCE_MEDIUM_THRESHOLD else "LOW"
        return ConfidenceBreakdown(overall_confidence=overall, level=level, components={
            "extraction_quality": round(extraction_quality,2),
            "validation_quality": round(validation_score,2),
            "match_confidence": round(match_score,2)})
