from typing import Optional
from app.schemas.extraction_schema import ExtractedActivity
from app.schemas.matching_schema import ScheduleTask
from app.schemas.response_schema import ProposedTaskUpdate


class ProposalGenerator:
    """Generates non-destructive progress proposals and never hides invalid overflows."""
    @staticmethod
    def generate(activity: ExtractedActivity, matched_task: Optional[ScheduleTask]) -> Optional[ProposedTaskUpdate]:
        if not matched_task or activity.quantity_completed is None:
            return None
        prev_qty = float(matched_task.previous_completed_quantity)
        reported_qty = float(activity.quantity_completed)
        planned_qty = float(matched_task.planned_quantity)
        new_completed = prev_qty + reported_qty
        warnings = []
        status = "PENDING_REVIEW"
        if planned_qty > 0 and new_completed > planned_qty:
            warnings.append(f"Proposed completed quantity exceeds planned quantity by {new_completed - planned_qty:.2f} {matched_task.unit}.")
            status = "REVIEW_REQUIRED"
        prev_progress = (prev_qty / planned_qty * 100.0) if planned_qty > 0 else 0.0
        proposed_progress = (new_completed / planned_qty * 100.0) if planned_qty > 0 else 0.0
        return ProposedTaskUpdate(
            task_id=matched_task.task_id, task_name=matched_task.task_name, unit=matched_task.unit,
            previous_completed_quantity=prev_qty, reported_quantity=reported_qty,
            proposed_completed_quantity=new_completed, planned_quantity=planned_qty,
            previous_progress_percent=round(min(100.0, max(0.0, prev_progress)), 2),
            proposed_progress_percent=round(min(100.0, max(0.0, proposed_progress)), 2),
            requires_human_approval=True, status=status, warnings=warnings,
            audit_notes=f"Calculated proposal: {prev_qty:.2f} + {reported_qty:.2f} = {new_completed:.2f}. Human sign-off required."
        )
