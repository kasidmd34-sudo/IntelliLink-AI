from typing import List, Optional
from app.schemas.extraction_schema import DocumentExtraction, ExtractedActivity
from app.schemas.matching_schema import ScheduleTask
from app.schemas.response_schema import ValidationReport


class ExtractionValidator:
    """Applies domain validation rules on extracted infrastructure activities."""

    STANDARD_UNITS = {"m", "metre", "meter", "km", "kilometre", "m2", "sqm", "m3", "cum", "mt", "ton", "nos", "%"}

    @classmethod
    def validate_activity(
        cls,
        activity: ExtractedActivity,
        matched_task: Optional[ScheduleTask] = None
    ) -> ValidationReport:
        warnings: List[str] = []
        errors: List[str] = []

        # 1. Activity Name
        if not activity.activity_name or len(activity.activity_name.strip()) < 2:
            errors.append("Activity name is missing or too short.")

        # 2. Quantity Boundaries
        if activity.quantity_completed is not None:
            if activity.quantity_completed < 0:
                errors.append(f"Quantity completed cannot be negative: {activity.quantity_completed}")

            if matched_task and activity.quantity_completed > matched_task.planned_quantity:
                warnings.append(
                    f"Reported quantity ({activity.quantity_completed} {activity.unit or ''}) exceeds "
                    f"total planned quantity ({matched_task.planned_quantity} {matched_task.unit}) for task '{matched_task.task_name}'."
                )

        # 2b. Cumulative consistency
        if activity.cumulative_quantity is not None and activity.quantity_completed is not None and activity.cumulative_quantity < activity.quantity_completed:
            warnings.append("Cumulative quantity is lower than the newly completed quantity; reviewer confirmation is required.")

        # 3. Unit Validation
        if activity.unit:
            norm_unit = activity.unit.lower().strip()
            if norm_unit not in cls.STANDARD_UNITS and not any(u in norm_unit for u in cls.STANDARD_UNITS):
                warnings.append(f"Non-standard unit detected: '{activity.unit}'.")

        if matched_task and activity.unit and matched_task.unit and activity.unit.lower().strip() != matched_task.unit.lower().strip():
            warnings.append(f"Extracted unit '{activity.unit}' differs from schedule unit '{matched_task.unit}'.")

        # 4. Progress Percentage
        if activity.reported_progress_percent is not None:
            if activity.reported_progress_percent < 0.0 or activity.reported_progress_percent > 100.0:
                errors.append(f"Reported progress % must be between 0 and 100: {activity.reported_progress_percent}")

        # 5. Evidence Audit
        if activity.quantity_completed is not None and not activity.source_evidence:
            warnings.append("Quantity was extracted without supporting source evidence excerpt.")

        return ValidationReport(is_valid=len(errors) == 0, warnings=warnings, errors=errors)

    @classmethod
    def validate_document(cls, extraction: DocumentExtraction) -> ValidationReport:
        warnings: List[str] = []
        errors: List[str] = []

        if not extraction.activities:
            warnings.append("No activities were detected in the document.")

        activity_names = [a.activity_name.lower().strip() for a in extraction.activities if a.activity_name]
        if len(activity_names) != len(set(activity_names)):
            warnings.append("Duplicate activities detected within the same document.")

        return ValidationReport(is_valid=len(errors) == 0, warnings=warnings, errors=errors)