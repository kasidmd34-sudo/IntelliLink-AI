import time
from typing import Optional

from app.ai.confidence import ConfidenceScorer
from app.ai.document_processor import DocumentProcessor
from app.ai.extractor import InfrastructureExtractor
from app.ai.issue_detector import IssueDetector
from app.ai.matcher import ScheduleMatcher
from app.ai.proposal_generator import ProposalGenerator
from app.ai.validator import ExtractionValidator

from app.schemas.response_schema import (
    DocumentProcessResponse,
    ProcessedActivityOutput,
)


class ProcessingService:
    """
    Orchestrates document ingestion, extraction, issue detection,
    validation, schedule matching, confidence scoring, and proposals.
    """

    def __init__(
        self,
        doc_processor: Optional[DocumentProcessor] = None,
        extractor: Optional[InfrastructureExtractor] = None,
        matcher: Optional[ScheduleMatcher] = None,
    ):
        self.doc_processor = doc_processor or DocumentProcessor()
        self.extractor = extractor or InfrastructureExtractor()
        self.matcher = matcher or ScheduleMatcher()
        self.validator = ExtractionValidator()
        self.issue_detector = IssueDetector()

    async def process_document_pipeline(
        self,
        file_bytes: bytes,
        filename: str,
        content_type: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> DocumentProcessResponse:

        start_time = time.time()

        # Step 1: Save and validate uploaded file
        meta = await self.doc_processor.save_and_validate(
            file_bytes=file_bytes,
            filename=filename,
            content_type=content_type,
            project_id=project_id,
        )

        # Step 2: Extract structured information using Gemini
        extraction = self.extractor.extract(
            file_path=meta["file_path"],
            project_id=project_id,
            mime_type=content_type,
        )

        # Step 3: PDF fallback
        # If direct document extraction fails, extract PDF text
        # and process that text instead.
        if (
            not extraction.activities
            or extraction.extraction_status == "FAILED"
        ) and meta.get("file_type") == "pdf":

            pdf_text = self.doc_processor.extract_text_fallback(
                meta["file_path"]
            )

            if pdf_text.strip():
                extraction = self.extractor.extract_from_text(
                    pdf_text,
                    project_id=project_id,
                )

        return self._build_process_response(
            extraction=extraction,
            document_id=meta["document_id"],
            filename=filename,
            file_type=meta["file_type"],
            project_id=project_id,
            start_time=start_time,
            raw_text=None,
        )

    def process_text_pipeline(
        self,
        text: str,
        project_id: Optional[str] = None,
    ) -> DocumentProcessResponse:

        start_time = time.time()
        doc_id = f"txt_{int(start_time * 1000)}"

        # Extract structured information from raw text
        extraction = self.extractor.extract_from_text(
            text=text,
            project_id=project_id,
        )

        return self._build_process_response(
            extraction=extraction,
            document_id=doc_id,
            filename="live_text_note.txt",
            file_type="txt",
            project_id=project_id,
            start_time=start_time,

            # IMPORTANT:
            # Pass original text so IssueDetector can independently
            # detect issues even when Gemini misses them.
            raw_text=text,
        )

    def _build_process_response(
        self,
        extraction,
        document_id: str,
        filename: str,
        file_type: str,
        project_id: Optional[str],
        start_time: float,
        raw_text: Optional[str] = None,
    ) -> DocumentProcessResponse:

        # ---------------------------------------------------------
        # STEP 1: Normalize issues extracted by Gemini
        # ---------------------------------------------------------
        normalized_global_issues = [
            self.issue_detector.normalize_issue(
                iss.original_text,
                iss.evidence,
            )
            for iss in extraction.document_level_issues
        ]

        # ---------------------------------------------------------
        # STEP 2: Independent global issue detection
        # ---------------------------------------------------------
        # If Gemini missed all global issues, scan the original text.
        if not normalized_global_issues and raw_text:
            normalized_global_issues = (
                self.issue_detector.detect_issues(raw_text)
            )

        document_validation = self.validator.validate_document(
            extraction
        )

        processed_activities = []

        # ---------------------------------------------------------
        # STEP 3: Process every extracted activity
        # ---------------------------------------------------------
        for activity in extraction.activities:

            # First normalize issues returned by Gemini
            standardized_issues = [
                self.issue_detector.normalize_issue(
                    iss.original_text,
                    iss.evidence,
                )
                for iss in activity.issues
            ]

            # -----------------------------------------------------
            # STEP 4: Fallback issue detection
            # -----------------------------------------------------
            # If Gemini returned no issues for this activity,
            # independently scan all available source evidence.
            if not standardized_issues:

                evidence_texts = []

                # Add activity-level source evidence
                for evidence in activity.source_evidence:
                    if evidence.verbatim_text:
                        evidence_texts.append(
                            evidence.verbatim_text
                        )

                # Add original raw text as a safety fallback
                if raw_text:
                    evidence_texts.append(raw_text)

                activity_source_text = " ".join(
                    evidence_texts
                ).strip()

                if activity_source_text:
                    standardized_issues = (
                        self.issue_detector.detect_issues(
                            activity_source_text
                        )
                    )

            # Store final detected issues
            activity.issues = standardized_issues

            # -----------------------------------------------------
            # STEP 5: Match activity with project schedule
            # -----------------------------------------------------
            match_result = self.matcher.match(
                activity_name=activity.activity_name,
                activity_code=activity.activity_code,
                location=activity.location,
                project_id=project_id or extraction.project_id,
            )

            best_match = match_result.best_match

            matched_task = (
                self.matcher.get_task_by_id(best_match.task_id)
                if best_match
                else None
            )

            # -----------------------------------------------------
            # STEP 6: Validate extracted activity
            # -----------------------------------------------------
            validation_report = self.validator.validate_activity(
                activity,
                matched_task=matched_task,
            )

            # -----------------------------------------------------
            # STEP 7: Calculate confidence
            # -----------------------------------------------------
            confidence = ConfidenceScorer.calculate(
                activity=activity,
                validation=validation_report,
                best_match=best_match,
            )

            # -----------------------------------------------------
            # STEP 8: Generate proposed schedule update
            # -----------------------------------------------------
            proposed_update = None

            if (
                validation_report.is_valid
                and confidence.level != "LOW"
                and match_result.match_status != "NO_MATCH"
            ):
                proposed_update = ProposalGenerator.generate(
                    activity,
                    matched_task=matched_task,
                )

            # -----------------------------------------------------
            # STEP 9: Create recommendation explanation
            # -----------------------------------------------------
            if best_match:
                recommend_reason = (
                    f"Recommended Task '{best_match.task_name}' "
                    f"({best_match.task_id}) with "
                    f"{best_match.score * 100:.1f}% confidence score."
                )
            else:
                recommend_reason = (
                    "No candidate task matched with sufficient confidence."
                )

            # -----------------------------------------------------
            # STEP 10: Add processed activity to final response
            # -----------------------------------------------------
            processed_activities.append(
                ProcessedActivityOutput(
                    extracted_activity=activity,
                    validation_report=validation_report,
                    recommended_task=best_match,
                    alternative_matches=match_result.alternatives,
                    confidence=confidence,
                    detected_issues=standardized_issues,
                    proposed_update=proposed_update,
                    recommendation_reason=recommend_reason,
                    requires_human_approval=True,
                )
            )

        # ---------------------------------------------------------
        # STEP 11: Final processing status
        # ---------------------------------------------------------
        elapsed = time.time() - start_time

        if processed_activities:
            status = "REVIEW_REQUIRED"
        elif extraction.extraction_status == "FAILED":
            status = "FAILED"
        else:
            status = "REVIEW_REQUIRED"

        # ---------------------------------------------------------
        # STEP 12: Audit trail
        # ---------------------------------------------------------
        audit_trail = {
            "document_id": document_id,
            "filename": filename,
            "activities_detected": len(processed_activities),
            "document_validation": document_validation.model_dump(),
            "processing_time_ms": round(elapsed * 1000, 2),
            "system": "IntelliLink AI Engine",
        }

        # ---------------------------------------------------------
        # STEP 13: Final API response
        # ---------------------------------------------------------
        return DocumentProcessResponse(
            document_id=document_id,
            filename=filename,
            file_type=file_type,
            project_id=project_id or extraction.project_id,
            status=status,
            processed_activities=processed_activities,
            global_issues=normalized_global_issues,
            execution_time_seconds=round(elapsed, 3),
            audit_trail=audit_trail,
        )