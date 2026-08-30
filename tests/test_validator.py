from app.ai.validator import ExtractionValidator
from app.schemas.extraction_schema import ExtractedActivity, SourceEvidence
from app.schemas.matching_schema import ScheduleTask


def test_validator_valid_activity():
    act = ExtractedActivity(
        activity_name="Bituminous Road Work",
        quantity_completed=420.0,
        unit="m",
        location="Km 12-18",
        source_evidence=[
            SourceEvidence(
                field_name="quantity_completed",
                extracted_value="420",
                verbatim_text="420 metres of bituminous road work completed"
            )
        ]
    )
    report = ExtractionValidator.validate_activity(act)
    assert report.is_valid is True
    assert len(report.errors) == 0


def test_validator_negative_quantity():
    act = ExtractedActivity(
        activity_name="Earthwork",
        quantity_completed=-150.0,
        unit="m3"
    )
    report = ExtractionValidator.validate_activity(act)
    assert report.is_valid is False
    assert any("negative" in err for err in report.errors)


def test_validator_quantity_exceeding_planned():
    task = ScheduleTask(
        project_id="P1",
        task_id="T04",
        task_name="Bituminous Road Work",
        unit="m",
        planned_quantity=1000.0,
        previous_completed_quantity=500.0
    )
    act = ExtractedActivity(
        activity_name="Bituminous Road Work",
        quantity_completed=1500.0,
        unit="m"
    )
    report = ExtractionValidator.validate_activity(act, matched_task=task)
    assert report.is_valid is True
    assert any("exceeds total planned quantity" in w for w in report.warnings)


def test_validator_invalid_progress_percentage():
    act = ExtractedActivity(
        activity_name="Paving",
        reported_progress_percent=125.0
    )
    report = ExtractionValidator.validate_activity(act)
    assert report.is_valid is False
    assert any("between 0 and 100" in err for err in report.errors)