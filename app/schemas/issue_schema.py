from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class IssueCategory(str, Enum):
    HEAVY_RAINFALL = "heavy_rainfall"
    LAND_ISSUE = "land_issue"
    MATERIAL_SHORTAGE = "material_shortage"
    LABOUR_SHORTAGE = "labour_shortage"
    APPROVAL_DELAY = "approval_delay"
    UTILITY_RELOCATION = "utility_relocation"
    SITE_ACCESS_PROBLEM = "site_access_problem"
    DESIGN_CHANGE = "design_change"
    CONTRACTOR_DELAY = "contractor_delay"
    QUALITY_CONCERN = "quality_concern"
    OTHER = "other"


class DetectedIssue(BaseModel):
    category: IssueCategory = Field(..., description="Controlled issue taxonomy category")
    original_text: str = Field(..., description="Exact textual excerpt from the document")
    evidence: Optional[str] = Field(None, description="Supporting sentence context")
    confidence: float = Field(default=1.0, ge=0.0, le=1.0, description="Detection confidence")