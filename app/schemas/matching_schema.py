from typing import List, Optional
from pydantic import BaseModel, Field


class ScheduleTask(BaseModel):
    project_id: str
    task_id: str
    task_name: str
    work_package: Optional[str] = None
    location_scope: Optional[str] = None
    unit: str
    planned_quantity: float
    previous_completed_quantity: float = 0.0
    aliases: List[str] = Field(default_factory=list)


class MatchCandidate(BaseModel):
    task_id: str
    task_name: str
    work_package: Optional[str] = None
    score: float = Field(..., ge=0.0, le=1.0)
    semantic_score: float = Field(..., ge=0.0, le=1.0)
    fuzzy_score: float = Field(..., ge=0.0, le=1.0)
    location_score: float = Field(default=0.0, ge=0.0, le=1.0)
    reasoning: str


class MatchResult(BaseModel):
    activity_name: str
    best_match: Optional[MatchCandidate] = None
    alternatives: List[MatchCandidate] = Field(default_factory=list)
    match_status: str = Field(..., description="CONFIDENT_MATCH, AMBIGUOUS, NO_MATCH")