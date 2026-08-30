from app.ai.fuzzy_matcher import FuzzyMatcher
from app.ai.matcher import ScheduleMatcher


def test_fuzzy_matcher_similarity():
    score = FuzzyMatcher.calculate_score("Bituminous Road Work", "Bituminous Road Work")
    assert score == 1.0

    score_alias = FuzzyMatcher.calculate_score(
        "road asphalt laying",
        "Bituminous Road Work",
        aliases=["road asphalt laying", "dense bituminous macadam"]
    )
    assert score_alias == 1.0

    score_unrelated = FuzzyMatcher.calculate_score("Bridge Construction", "Thermoplastic Road Marking")
    assert score_unrelated <= 0.40


def test_matcher_exact_code_match(mock_schedule):
    matcher = ScheduleMatcher(schedule_tasks=mock_schedule)
    result = matcher.match(activity_name="Random String", activity_code="T04")
    assert result.best_match is not None
    assert result.best_match.task_id == "T04"
    assert result.best_match.score >= 0.90


def test_matcher_semantic_paraphrase(mock_schedule):
    matcher = ScheduleMatcher(schedule_tasks=mock_schedule)
    result = matcher.match(activity_name="Road asphalt laying")
    assert result.best_match is not None
    assert result.best_match.task_id == "T04"
    assert result.best_match.score >= 0.70


def test_matcher_low_confidence_unrelated_task(mock_schedule):
    matcher = ScheduleMatcher(schedule_tasks=mock_schedule)
    result = matcher.match(activity_name="Underwater submarine cabling")
    assert result.best_match is None or result.match_status in ["AMBIGUOUS", "NO_MATCH"]


def test_matcher_empty_schedule():
    matcher = ScheduleMatcher(schedule_tasks=[])
    result = matcher.match(activity_name="Bituminous Road Work")
    assert result.match_status == "NO_MATCH"
    assert result.best_match is None
    assert len(result.alternatives) == 0