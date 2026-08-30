from typing import List
# pyrefly: ignore [missing-import]
from rapidfuzz import fuzz
from app.utils.text_utils import normalize_text


class FuzzyMatcher:
    """Calculates normalized token ratio score using RapidFuzz."""

    @staticmethod
    def calculate_score(query: str, target: str, aliases: List[str] | None = None) -> float:
        norm_query = normalize_text(query)
        norm_target = normalize_text(target)

        if not norm_query or not norm_target:
            return 0.0

        base_score = max(
            fuzz.token_sort_ratio(norm_query, norm_target),
            fuzz.token_set_ratio(norm_query, norm_target)
        ) / 100.0

        alias_scores = [
            max(
                fuzz.token_sort_ratio(norm_query, normalize_text(alias)),
                fuzz.token_set_ratio(norm_query, normalize_text(alias))
            ) / 100.0
            for alias in (aliases or [])
            if alias
        ]
        return max([base_score] + alias_scores)