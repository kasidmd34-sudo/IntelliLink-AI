from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.schemas.extraction_schema import ExtractedActivity
from app.schemas.issue_schema import DetectedIssue
from app.schemas.matching_schema import MatchCandidate


class ValidationReport(BaseModel):
    is_valid: bool
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class ConfidenceBreakdown(BaseModel):
    overall_confidence: float = Field(..., ge=0.0, le=1.0)
    level: str = Field(..., description="HIGH, MEDIUM, LOW")
    components: Dict[str, float] = Field(default_factory=dict)


class ProposedTaskUpdate(BaseModel):
    task_id: str
    task_name: str
    unit: str
    previous_completed_quantity: float
    reported_quantity: float
    proposed_completed_quantity: float
    planned_quantity: float
    previous_progress_percent: float
    proposed_progress_percent: float
    requires_human_approval: bool = True
    audit_notes: str
    status: str = "PENDING_REVIEW"
    warnings: List[str] = Field(default_factory=list)


class ProcessedActivityOutput(BaseModel):
    extracted_activity: ExtractedActivity
    validation_report: ValidationReport
    recommended_task: Optional[MatchCandidate] = None
    alternative_matches: List[MatchCandidate] = Field(default_factory=list)
    confidence: ConfidenceBreakdown
    detected_issues: List[DetectedIssue] = Field(default_factory=list)
    proposed_update: Optional[ProposedTaskUpdate] = None
    recommendation_reason: str
    requires_human_approval: bool = True


class DocumentProcessResponse(BaseModel):
    document_id: str
    filename: str
    file_type: str
    project_id: Optional[str] = None
    status: str = Field(..., description="PROCESSED, REVIEW_REQUIRED, FAILED")
    processed_activities: List[ProcessedActivityOutput] = Field(default_factory=list)
    global_issues: List[DetectedIssue] = Field(default_factory=list)
    execution_time_seconds: float
    audit_trail: Dict[str, Any] = Field(default_factory=dict)