import pytest
from app.ai.confidence import ConfidenceScorer
from app.ai.issue_detector import IssueDetector
from app.ai.proposal_generator import ProposalGenerator
from app.ai.validator import ExtractionValidator
from app.schemas.extraction_schema import ExtractedActivity, SourceEvidence
from app.schemas.issue_schema import IssueCategory


@pytest.mark.asyncio
async def test_end_to_end_demonstration_scenario(mock_schedule, matcher):
    """
    Validates the end-to-end hackathon workflow:
    Input: "420 metres of bituminous road work was completed between Km 12 and Km 18. Progress was affected by heavy rainfall."
    Prior: T04 (3,780 / 6,000 m = 63%)
    Expected Proposed: 4,200 / 6,000 m = 70%
    """
    # 1. Extracted activity
    activity = ExtractedActivity(
        activity_name="Bituminous Road Work",
        quantity_completed=420.0,
        unit="m",
        location="Km 12-18",
        source_evidence=[
            SourceEvidence(
                field_name="quantity_completed",
                extracted_value="420",
                verbatim_text="420 metres of bituminous road work was completed between Km 12 and Km 18"
            )
        ]
    )

    # 2. Detect issue
    issue = IssueDetector.normalize_issue(
        raw_text="Progress was affected by heavy rainfall",
        evidence="heavy rainfall"
    )
    assert issue.category == IssueCategory.HEAVY_RAINFALL

    # 3. Match schedule
    match_result = matcher.match(
        activity_name=activity.activity_name,
        location=activity.location,
        project_id="PROJECT_001"
    )
    assert match_result.best_match.task_id == "T04"

    # 4. Validate activity
    matched_task = matcher.get_task_by_id(match_result.best_match.task_id)
    val_rep = ExtractionValidator.validate_activity(activity, matched_task=matched_task)
    assert val_rep.is_valid is True

    # 5. Confidence scoring
    confidence = ConfidenceScorer.calculate(activity, val_rep, match_result.best_match)
    assert confidence.overall_confidence >= 0.85
    assert confidence.level in ["HIGH", "MEDIUM"]

    # 6. Generate proposed update
    proposal = ProposalGenerator.generate(activity, matched_task)
    assert proposal is not None
    assert proposal.task_id == "T04"
    assert proposal.previous_completed_quantity == 3780.0
    assert proposal.reported_quantity == 420.0
    assert proposal.proposed_completed_quantity == 4200.0
    assert proposal.planned_quantity == 6000.0
    assert proposal.proposed_progress_percent == 70.0
    assert proposal.requires_human_approval is True