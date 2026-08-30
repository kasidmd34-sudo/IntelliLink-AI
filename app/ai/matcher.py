from pathlib import Path
from typing import List, Optional
import pandas as pd
from app.ai.fuzzy_matcher import FuzzyMatcher
from app.ai.semantic_matcher import SemanticMatcher
from app.config.settings import get_settings
from app.schemas.matching_schema import MatchCandidate, MatchResult, ScheduleTask
from app.utils.text_utils import normalize_text

settings = get_settings()


class ScheduleMatcher:
    """Hybrid schedule matching engine combining Exact, Fuzzy, Semantic, and Context matching."""

    def __init__(
        self,
        schedule_tasks: Optional[List[ScheduleTask]] = None,
        schedule_csv_path: Optional[Path] = None,
        semantic_matcher: Optional[SemanticMatcher] = None
    ):
        self.semantic_matcher = semantic_matcher or SemanticMatcher()
        if schedule_tasks is not None:
            self.tasks = schedule_tasks
        elif schedule_csv_path and Path(schedule_csv_path).exists():
            self.tasks = []
            self.load_schedule_from_csv(schedule_csv_path)
        elif settings.SCHEDULE_DATA_PATH.exists():
            self.tasks = []
            self.load_schedule_from_csv(settings.SCHEDULE_DATA_PATH)
        else:
            self.tasks = []

    def load_schedule_from_csv(self, csv_path: Path):
        df = pd.read_csv(csv_path)
        self.tasks = []
        for _, row in df.iterrows():
            aliases = [a.strip() for a in str(row.get("aliases", "")).split(";")] if pd.notna(row.get("aliases")) else []
            task = ScheduleTask(
                project_id=str(row["project_id"]),
                task_id=str(row["task_id"]),
                task_name=str(row["task_name"]),
                work_package=str(row.get("work_package", "")) if pd.notna(row.get("work_package")) else None,
                location_scope=str(row.get("location_scope", "")) if pd.notna(row.get("location_scope")) else None,
                unit=str(row.get("unit", "m")),
                planned_quantity=float(row.get("planned_quantity", 0.0)),
                previous_completed_quantity=float(row.get("previous_completed_quantity", 0.0)),
                aliases=aliases
            )
            self.tasks.append(task)

    def match(
        self,
        activity_name: str,
        activity_code: Optional[str] = None,
        location: Optional[str] = None,
        project_id: Optional[str] = None,
        top_k: int = 3
    ) -> MatchResult:
        if not self.tasks:
            return MatchResult(activity_name=activity_name, best_match=None, alternatives=[], match_status="NO_MATCH")

        candidate_tasks = [t for t in self.tasks if not project_id or t.project_id == project_id]
        if project_id and not candidate_tasks:
            return MatchResult(activity_name=activity_name, best_match=None, alternatives=[], match_status="NO_MATCH")
        all_descriptions = []
        task_phrase_indices = []
        for task in candidate_tasks:
            phrases = [task.task_name]
            if task.work_package:
                phrases.append(f"{task.task_name} {task.work_package}")
            for a in task.aliases:
                if a:
                    phrases.append(a)
            start_idx = len(all_descriptions)
            all_descriptions.extend(phrases)
            end_idx = len(all_descriptions)
            task_phrase_indices.append((start_idx, end_idx))

        raw_semantic_scores = self.semantic_matcher.compute_similarity(activity_name, all_descriptions)
        semantic_scores = [
            max(raw_semantic_scores[s:e]) if s < e else 0.0
            for (s, e) in task_phrase_indices
        ]

        candidates: List[MatchCandidate] = []
        norm_query = normalize_text(activity_name)

        for i, task in enumerate(candidate_tasks):
            norm_task_name = normalize_text(task.task_name)
            is_exact = (norm_query == norm_task_name) or (activity_code and activity_code.strip().upper() == task.task_id.upper())

            fuzzy_score = 1.0 if is_exact else FuzzyMatcher.calculate_score(activity_name, task.task_name, task.aliases)
            semantic_score = 1.0 if is_exact else semantic_scores[i]

            location_score = 0.5
            if location and task.location_scope:
                norm_loc = normalize_text(location)
                norm_scope = normalize_text(task.location_scope)
                location_score = 1.0 if (norm_loc in norm_scope or norm_scope in norm_loc) else 0.2
            elif not location:
                location_score = 1.0 if is_exact else 0.5

            project_score = 1.0 if (project_id and task.project_id == project_id) else (1.0 if is_exact else 0.5)

            if is_exact:
                final_score = 1.0
            else:
                final_score = (
                    settings.WEIGHT_SEMANTIC * semantic_score +
                    settings.WEIGHT_FUZZY * fuzzy_score +
                    settings.WEIGHT_LOCATION * location_score +
                    settings.WEIGHT_PROJECT * project_score +
                    settings.WEIGHT_DATE * 0.5
                )
            final_score = round(min(1.0, max(0.0, final_score)), 4)

            reasoning = f"Semantic={semantic_score:.2f}, Fuzzy={fuzzy_score:.2f}, Location={location_score:.2f}"

            candidates.append(
                MatchCandidate(
                    task_id=task.task_id,
                    task_name=task.task_name,
                    work_package=task.work_package,
                    score=final_score,
                    semantic_score=semantic_score,
                    fuzzy_score=fuzzy_score,
                    location_score=location_score,
                    reasoning=reasoning
                )
            )

        candidates.sort(key=lambda c: c.score, reverse=True)
        top_candidates = candidates[:top_k]
        best_match = top_candidates[0] if top_candidates else None

        if best_match and best_match.score >= settings.CONFIDENCE_HIGH_THRESHOLD:
            status = "CONFIDENT_MATCH"
        elif best_match and best_match.score >= settings.CONFIDENCE_MEDIUM_THRESHOLD:
            status = "AMBIGUOUS"
        else:
            status = "NO_MATCH"

        return MatchResult(activity_name=activity_name, best_match=best_match, alternatives=top_candidates[1:] if best_match else [], match_status=status)

    def get_task_by_id(self, task_id: str) -> Optional[ScheduleTask]:
        return next((t for t in self.tasks if t.task_id == task_id), None)