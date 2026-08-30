from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field
from app.schemas.issue_schema import DetectedIssue


class SourceEvidence(BaseModel):
    field_name: str = Field(..., description="Field supported by evidence")
    extracted_value: str = Field(..., description="Extracted textual or numeric value")
    verbatim_text: str = Field(..., description="Verbatim quote from the document")
    page_number: Optional[int] = Field(None, description="Page number reference")


class ExtractedActivity(BaseModel):
    activity_name: str = Field(..., description="Name of the infrastructure task or activity")
    activity_code: Optional[str] = Field(None, description="BOQ or schedule item code")
    work_package: Optional[str] = Field(None, description="Associated work package")
    location: Optional[str] = Field(None, description="Chainage, span, or site reference (e.g. Km 12-18)")
    quantity_completed: Optional[float] = Field(None, description="Newly completed quantity")
    cumulative_quantity: Optional[float] = Field(None, description="Cumulative quantity to date")
    unit: Optional[str] = Field(None, description="Unit of measurement (m, m3, nos, etc.)")
    reported_progress_percent: Optional[float] = Field(None, description="Reported % progress")
    issues: List[DetectedIssue] = Field(default_factory=list, description="Activity-specific issues")
    observations: List[str] = Field(default_factory=list, description="Field and quality remarks")
    source_evidence: List[SourceEvidence] = Field(default_factory=list, description="Audit evidence citations")


class DocumentExtraction(BaseModel):
    project_name: Optional[str] = Field(None, description="Identified project title")
    project_id: Optional[str] = Field(None, description="Project code or identifier")
    report_date: Optional[date] = Field(None, description="Report or measurement date")
    contractor_name: Optional[str] = Field(None, description="Contractor entity name")
    activities: List[ExtractedActivity] = Field(default_factory=list, description="Extracted activities")
    document_level_issues: List[DetectedIssue] = Field(default_factory=list, description="General project issues")
    extraction_notes: Optional[str] = Field(None, description="Ambiguity or extraction notes")
    extraction_status: str = Field(default="SUCCESS", description="SUCCESS, PARTIAL, or FAILED")