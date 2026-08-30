"""
IntelliLink AI - Infrastructure Dataset Generator
Generates realistic labeled documents with a 70% dev / 15% val / 15% test split.
"""

import json
import random
from pathlib import Path
from typing import Any, Dict, List

DATA_DIR = Path(__file__).resolve().parent
EVAL_DIR = DATA_DIR / "evaluation"
EVAL_DIR.mkdir(parents=True, exist_ok=True)

INFRASTRUCTURE_ACTIVITIES = [
    {
        "task_id": "T01",
        "name": "Site Clearance & Grubbing",
        "unit": "m2",
        "qty_range": (5000, 20000),
        "loc_template": "Km {s}-{e}",
        "templates": [
            "Site clearance and grubbing of {qty} m2 was carried out between {loc}.",
            "Completed grubbing and site preparation over an area of {qty} m2 at {loc}.",
            "Contractor cleared {qty} m2 of land along {loc} for roadway expansion."
        ],
        "aliases": ["site preparation", "land clearing", "grubbing work"]
    },
    {
        "task_id": "T02",
        "name": "Earthwork in Embankment",
        "unit": "m3",
        "qty_range": (1000, 8000),
        "loc_template": "Km {s}-{e}",
        "templates": [
            "Earthwork filling in embankment of {qty} m3 completed at {loc}.",
            "Subgrade soil compaction and embankment earthwork completed: {qty} m3 between {loc}.",
            "{qty} m3 of earth movement and embankment construction completed in sector {loc}."
        ],
        "aliases": ["embankment filling", "soil compaction", "earth filling"]
    },
    {
        "task_id": "T03",
        "name": "Sub-base Drainage Layer",
        "unit": "m3",
        "qty_range": (500, 3000),
        "loc_template": "Km {s}-{e}",
        "templates": [
            "Granular sub-base drainage layer laid for {qty} m3 from {loc}.",
            "Completed {qty} m3 of GSB sub-base drainage layer along {loc}.",
            "Drainage blanket and sub-base work progress: {qty} m3 at {loc}."
        ],
        "aliases": ["GSB laying", "drainage layer", "granular sub base"]
    },
    {
        "task_id": "T04",
        "name": "Bituminous Road Work",
        "unit": "m",
        "qty_range": (200, 1500),
        "loc_template": "Km {s}-{e}",
        "templates": [
            "During the reporting period, {qty} metres of bituminous road work was completed between {loc}.",
            "Dense Bituminous Macadam (DBM) asphalt laying executed for {qty} m at {loc}.",
            "Bituminous concrete wearing course laid over {qty} m between {loc}."
        ],
        "aliases": ["asphalt paving", "DBM laying", "road asphalt laying", "bituminous concrete"]
    },
    {
        "task_id": "T05",
        "name": "Thermoplastic Road Marking",
        "unit": "m",
        "qty_range": (1000, 6000),
        "loc_template": "Km {s}-{e}",
        "templates": [
            "Applied {qty} m of reflective thermoplastic road markings between {loc}.",
            "Lane marking and striping completed for {qty} m along {loc}.",
            "Thermoplastic paint application: {qty} m executed at {loc}."
        ],
        "aliases": ["lane striping", "road painting", "reflective marking"]
    },
    {
        "task_id": "T06",
        "name": "Reinforced Concrete Culvert",
        "unit": "nos",
        "qty_range": (1, 4),
        "loc_template": "Km {s}",
        "templates": [
            "Constructed and cured {qty} nos of Reinforced Concrete Box Culvert at {loc}.",
            "Structural RCC culvert installation completed: {qty} nos at {loc}.",
            "{qty} nos precast concrete culvert units erected at {loc}."
        ],
        "aliases": ["RCC box culvert", "pipe culvert", "slab culvert"]
    }
]

ISSUES_POOL = [
    {"category": "heavy_rainfall", "phrase": "Progress was severely affected by heavy rainfall and waterlogging."},
    {"category": "labour_shortage", "phrase": "Work was slowed down due to seasonal labour shortage."},
    {"category": "material_shortage", "phrase": "Bitumen and cement delivery delay caused partial stoppage."},
    {"category": "site_access_problem", "phrase": "Access road blockage delayed movement of dumpers."},
    {"category": "approval_delay", "phrase": "Pending safety clearance and local authority approval delayed operations."},
    {"category": "utility_relocation", "phrase": "Electric line relocation is obstructing continuous progress."},
    {"category": "land_issue", "phrase": "Right of way clearance dispute at adjacent plot hindered earthwork."}
]


def generate_dataset(num_samples: int = 60) -> List[Dict[str, Any]]:
    random.seed(42)
    samples = []

    for i in range(1, num_samples + 1):
        act_info = random.choice(INFRASTRUCTURE_ACTIVITIES)
        s_km = random.randint(1, 40)
        e_km = s_km + random.randint(2, 6)
        loc = act_info["loc_template"].format(s=s_km, e=e_km)
        qty = random.randint(act_info["qty_range"][0], act_info["qty_range"][1])

        use_alias = random.random() < 0.4
        act_name_used = random.choice(act_info["aliases"]) if (use_alias and act_info["aliases"]) else act_info["name"]

        base_template = random.choice(act_info["templates"])
        text = base_template.format(qty=qty, loc=loc)

        has_issue = random.random() < 0.5
        detected_issues = []
        if has_issue:
            issue_item = random.choice(ISSUES_POOL)
            text += f" {issue_item['phrase']}"
            detected_issues.append({
                "category": issue_item["category"],
                "original_text": issue_item["phrase"],
                "evidence": issue_item["phrase"]
            })

        sample = {
            "sample_id": f"INTL_DOC_{i:03d}",
            "project_id": "PROJECT_001",
            "text": text,
            "expected_extraction": {
                "project_name": "NH-48 Corridor Expansion",
                "activities": [
                    {
                        "activity_name": act_name_used,
                        "quantity_completed": float(qty),
                        "unit": act_info["unit"],
                        "location": loc,
                        "issues": detected_issues,
                        "source_evidence": [
                            {
                                "field_name": "quantity_completed",
                                "extracted_value": str(qty),
                                "verbatim_text": text
                            }
                        ]
                    }
                ]
            },
            "expected_task_id": act_info["task_id"]
        }
        samples.append(sample)

    return samples


def create_and_save_splits():
    dataset = generate_dataset(60)

    # 70% dev (42), 15% val (9), 15% test (9)
    dev_split = dataset[:42]
    val_split = dataset[42:51]
    test_split = dataset[51:]

    with open(EVAL_DIR / "dev_dataset.json", "w", encoding="utf-8") as f:
        json.dump(dev_split, f, indent=2)

    with open(EVAL_DIR / "val_dataset.json", "w", encoding="utf-8") as f:
        json.dump(val_split, f, indent=2)

    with open(EVAL_DIR / "test_dataset.json", "w", encoding="utf-8") as f:
        json.dump(test_split, f, indent=2)

    with open(EVAL_DIR / "evaluation_dataset.json", "w", encoding="utf-8") as f:
        json.dump(dataset, f, indent=2)

    print(f"Generated {len(dataset)} samples across dev (42), val (9), and test (9) splits.")


if __name__ == "__main__":
    create_and_save_splits()