import logging
from typing import List, Optional

from fastapi import (
    APIRouter,
    File,
    Form,
    HTTPException,
    UploadFile,
    status,
)
from pydantic import BaseModel, Field

from app.schemas.matching_schema import MatchResult, ScheduleTask
from app.schemas.response_schema import DocumentProcessResponse
from app.services.processing_service import ProcessingService


logger = logging.getLogger(__name__)

router = APIRouter(tags=["AI Processing"])

processing_service = ProcessingService()


class MatchScheduleRequest(BaseModel):
    project_id: str = Field(default="PROJECT_001")
    activity_name: str
    activity_code: Optional[str] = None
    location: Optional[str] = None


class ProcessTextRequest(BaseModel):
    project_id: Optional[str] = Field(default="PROJECT_001")
    text: str = Field(
        ...,
        description="Progress note or inspection text",
    )


class ProposalApprovalRequest(BaseModel):
    task_id: str
    approved_quantity: float
    reviewer_name: str = "Project Engineer (SIH Lead)"
    comments: Optional[str] = (
        "Verified with physical measurement sheet."
    )


@router.post(
    "/process-document",
    response_model=DocumentProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process document and generate review proposals",
)
@router.post(
    "/api/process-document",
    response_model=DocumentProcessResponse,
    include_in_schema=False,
)
async def process_document(
    file: UploadFile = File(...),
    project_id: Optional[str] = Form(None),
):
    try:
        logger.info(
            "Received document processing request. "
            "Filename=%s, Project=%s",
            file.filename,
            project_id,
        )

        content = await file.read()

        if not content:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        result = await processing_service.process_document_pipeline(
            file_bytes=content,
            filename=file.filename or "uploaded_doc",
            content_type=file.content_type,
            project_id=project_id,
        )

        logger.info(
            "Document processing completed successfully. "
            "Document ID=%s, Activities=%d",
            result.document_id,
            len(result.processed_activities),
        )

        return result

    except HTTPException:
        raise

    except ValueError as val_err:
        logger.warning(
            "Document validation error: %s",
            str(val_err),
        )

        raise HTTPException(
            status_code=422,
            detail=str(val_err),
        )

    except Exception as exc:
        logger.exception(
            "FULL ERROR IN /process-document"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Processing failed: {str(exc)}",
        )


@router.post(
    "/process-text",
    response_model=DocumentProcessResponse,
    status_code=status.HTTP_200_OK,
    summary="Process raw progress text notes and generate proposals",
)
@router.post(
    "/api/process-text",
    response_model=DocumentProcessResponse,
    include_in_schema=False,
)
async def process_text(req: ProcessTextRequest):
    try:
        if not req.text.strip():
            raise HTTPException(
                status_code=400,
                detail="Text field cannot be empty.",
            )

        logger.info(
            "Received text processing request. "
            "Project=%s, Text length=%d",
            req.project_id,
            len(req.text),
        )

        result = processing_service.process_text_pipeline(
            text=req.text,
            project_id=req.project_id,
        )

        logger.info(
            "Text processing completed successfully. "
            "Activities=%d, Status=%s",
            len(result.processed_activities),
            result.status,
        )

        return result

    except HTTPException:
        raise

    except Exception as exc:
        # This prints the COMPLETE traceback in the terminal.
        logger.exception(
            "FULL ERROR IN /process-text"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Text processing failure: {str(exc)}",
        )


@router.post(
    "/match-schedule",
    response_model=MatchResult,
    status_code=status.HTTP_200_OK,
    summary="Match activity string against schedule tasks",
)
@router.post(
    "/api/match-schedule",
    response_model=MatchResult,
    include_in_schema=False,
)
async def match_schedule(req: MatchScheduleRequest):
    try:
        logger.info(
            "Schedule matching request. "
            "Activity=%s, Project=%s",
            req.activity_name,
            req.project_id,
        )

        return processing_service.matcher.match(
            activity_name=req.activity_name,
            activity_code=req.activity_code,
            location=req.location,
            project_id=req.project_id,
        )

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "FULL ERROR IN /match-schedule"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Matching failure: {str(exc)}",
        )


@router.get(
    "/schedule-tasks",
    response_model=List[ScheduleTask],
    summary="Retrieve list of all official project schedule tasks",
)
@router.get(
    "/api/schedule-tasks",
    response_model=List[ScheduleTask],
    include_in_schema=False,
)
async def get_schedule_tasks():
    try:
        return processing_service.matcher.tasks

    except Exception as exc:
        logger.exception(
            "FULL ERROR IN /schedule-tasks"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve schedule tasks: {str(exc)}",
        )


@router.get(
    "/sample-documents",
    summary="Get curated realistic sample reports for instant live demonstration",
)
@router.get(
    "/api/sample-documents",
    include_in_schema=False,
)
async def get_sample_documents():
    return [
        {
            "id": "DEMO-01",
            "title": "NH-48 Daily Paving & Weather Disruption Note",
            "project_id": "PROJECT_001",
            "text": (
                "During the reporting period, 420 metres of "
                "bituminous road work was completed between "
                "Km 12 and Km 18. Progress was affected by "
                "heavy rainfall."
            ),
            "expected_task": "T04 - Bituminous Road Work",
            "expected_issue": "heavy_rainfall",
        },
        {
            "id": "DEMO-02",
            "title": "Embankment Earthwork & Manpower Delay",
            "project_id": "PROJECT_001",
            "text": (
                "Subcontractor completed 1,500 m3 of Earthwork "
                "in Embankment at Km 22. Work halted due to "
                "unexpected labour shortage."
            ),
            "expected_task": "T02 - Earthwork in Embankment",
            "expected_issue": "labour_shortage",
        },
        {
            "id": "DEMO-03",
            "title": "RCC Box Culvert Span Inspection",
            "project_id": "PROJECT_001",
            "text": (
                "Constructed and cured 2 nos of Reinforced "
                "Concrete Box Culvert at Km 15 bridge approach "
                "according to IRC specifications."
            ),
            "expected_task": "T06 - Reinforced Concrete Culvert",
            "expected_issue": "none",
        },
        {
            "id": "DEMO-04",
            "title": "Site Clearance & Grubbing Progress",
            "project_id": "PROJECT_001",
            "text": (
                "Completed grubbing and site preparation over "
                "an area of 8,500 m2 at Km 0-10. Right of way "
                "clearance dispute delayed southern boundary."
            ),
            "expected_task": "T01 - Site Clearance & Grubbing",
            "expected_issue": "land_issue",
        },
    ]


@router.post(
    "/approve-proposal",
    summary="Human Reviewer Sign-Off on AI Proposal (Non-destructive update)",
)
@router.post(
    "/api/approve-proposal",
    include_in_schema=False,
)
async def approve_proposal(req: ProposalApprovalRequest):
    try:
        task = processing_service.matcher.get_task_by_id(
            req.task_id
        )

        if not task:
            raise HTTPException(
                status_code=404,
                detail=f"Task with ID '{req.task_id}' not found.",
            )

        if req.approved_quantity < 0:
            raise HTTPException(
                status_code=422,
                detail="Approved quantity cannot be negative.",
            )

        if (
            task.planned_quantity > 0
            and req.approved_quantity > task.planned_quantity
        ):
            raise HTTPException(
                status_code=422,
                detail=(
                    "Approved quantity exceeds planned quantity; "
                    "correct it before approval."
                ),
            )

        previous_completed = task.previous_completed_quantity

        progress_percent = round(
            (
                req.approved_quantity
                / task.planned_quantity
                * 100.0
            )
            if task.planned_quantity > 0
            else 0.0,
            2,
        )

        return {
            "status": "APPROVED_EVENT_CREATED",
            "task_id": task.task_id,
            "task_name": task.task_name,
            "unit": task.unit,
            "previous_completed_quantity": previous_completed,
            "approved_completed_quantity": req.approved_quantity,
            "planned_quantity": task.planned_quantity,
            "progress_percent": progress_percent,
            "signed_by": req.reviewer_name,
            "reviewer_comments": req.comments,
            "audit_status": "PENDING_PERSISTENCE",
        }

    except HTTPException:
        raise

    except Exception as exc:
        logger.exception(
            "FULL ERROR IN /approve-proposal"
        )

        raise HTTPException(
            status_code=500,
            detail=f"Proposal approval failure: {str(exc)}",
        )