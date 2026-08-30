import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score
from app.ai.matcher import ScheduleMatcher
from app.ai.validator import ExtractionValidator
from app.schemas.extraction_schema import ExtractedActivity


def run_evaluation(ground_truth_path: str | Path | None = None):
    if ground_truth_path is None:
        ground_truth_path = BASE_DIR / "data" / "labels" / "sample_ground_truth.json"
    else:
        ground_truth_path = Path(ground_truth_path)

    with open(ground_truth_path, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    matcher = ScheduleMatcher()
    results = []
    y_true_issues = []
    y_pred_issues = []

    top1_correct = 0
    top3_correct = 0
    total_samples = len(dataset)

    for item in dataset:
        expected_act = item["expected_extraction"]["activities"][0]
        expected_task_id = item["expected_task_id"]

        match_res = matcher.match(
            activity_name=expected_act["activity_name"],
            location=expected_act.get("location")
        )

        candidates = [c.task_id for c in match_res.alternatives]
        top1_match = match_res.best_match.task_id if match_res.best_match else None

        if top1_match == expected_task_id:
            top1_correct += 1
        if expected_task_id in candidates[:3]:
            top3_correct += 1

        act_obj = ExtractedActivity(**expected_act)
        val_rep = ExtractionValidator.validate_activity(act_obj)

        has_issue_true = 1 if expected_act.get("issues") else 0
        has_issue_pred = 1 if act_obj.issues else 0
        y_true_issues.append(has_issue_true)
        y_pred_issues.append(has_issue_pred)

        results.append({
            "sample_id": item["sample_id"],
            "expected_task": expected_task_id,
            "matched_task": top1_match,
            "top1_hit": top1_match == expected_task_id,
            "top3_hit": expected_task_id in candidates[:3],
            "validation_passed": val_rep.is_valid
        })

    report = {
        "total_samples": total_samples,
        "schedule_top1_accuracy": round(top1_correct / total_samples, 4),
        "schedule_top3_accuracy": round(top3_correct / total_samples, 4),
        "issue_precision": round(precision_score(y_true_issues, y_pred_issues, zero_division=1), 4),
        "issue_recall": round(recall_score(y_true_issues, y_pred_issues, zero_division=1), 4),
        "issue_f1": round(f1_score(y_true_issues, y_pred_issues, zero_division=1), 4),
    }

    eval_dir = BASE_DIR / "data" / "evaluation"
    eval_dir.mkdir(parents=True, exist_ok=True)
    with open(eval_dir / "evaluation_report.json", "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    pd.DataFrame(results).to_csv(eval_dir / "evaluation_results.csv", index=False)
    print("IntelliLink AI Evaluation Completed:")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    run_evaluation()