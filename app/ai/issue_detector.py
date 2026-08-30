import re

from app.schemas.issue_schema import DetectedIssue, IssueCategory


KEYWORD_MAP = {
    IssueCategory.HEAVY_RAINFALL: [
        "rain",
        "rainfall",
        "monsoon",
        "downpour",
        "waterlogging",
        "inundation",
        "flooding",
    ],
    IssueCategory.LAND_ISSUE: [
        "land acquisition",
        "encroachment",
        "row clearance",
        "right of way",
        "land dispute",
        "landowner",
    ],
    IssueCategory.MATERIAL_SHORTAGE: [
        "cement shortage",
        "bitumen shortage",
        "aggregate delay",
        "raw material",
        "stockout",
    ],
    IssueCategory.LABOUR_SHORTAGE: [
        "labour shortage",
        "labor shortage",
        "strike",
        "manpower deficiency",
        "worker absence",
    ],
    IssueCategory.APPROVAL_DELAY: [
        "noc pending",
        "approval delay",
        "forest clearance",
        "railway clearance",
        "authority permit",
    ],
    IssueCategory.UTILITY_RELOCATION: [
        "utility shifting",
        "electric pole",
        "water pipeline",
        "gas line",
        "cable relocation",
    ],
    IssueCategory.SITE_ACCESS_PROBLEM: [
        "access blocked",
        "approach road",
        "traffic diversion",
        "site inaccessible",
    ],
    IssueCategory.DESIGN_CHANGE: [
        "drawing revision",
        "design amendment",
        "alignment change",
        "structural modification",
    ],
    IssueCategory.CONTRACTOR_DELAY: [
        "subcontractor delay",
        "equipment breakdown",
        "machinery failure",
        "slow mobilization",
    ],
    IssueCategory.QUALITY_CONCERN: [
        "honeycombing",
        "crack",
        "failed test",
        "cube failure",
        "rejection",
        "rework",
    ],
}


class IssueDetector:
    """Maps text into the controlled IntelliLink issue taxonomy."""

    @staticmethod
    def normalize_issue(
        raw_text: str,
        evidence: str | None = None,
    ) -> DetectedIssue:

        text = f"{raw_text} {evidence or ''}".lower()

        for category, keywords in KEYWORD_MAP.items():
            for keyword in keywords:
                if re.search(
                    r"\b" + re.escape(keyword) + r"\b",
                    text,
                ):
                    return DetectedIssue(
                        category=category,
                        original_text=raw_text,
                        evidence=evidence or raw_text,
                        confidence=0.95,
                    )

        return DetectedIssue(
            category=IssueCategory.OTHER,
            original_text=raw_text,
            evidence=evidence or raw_text,
            confidence=0.70,
        )

    @staticmethod
    def detect_issues(text: str) -> list[DetectedIssue]:
        """Find specific sentences containing explicit project issues."""

        if not text:
            return []

        sentences = re.split(
            r"(?<=[.!?])\s+|\n+",
            text,
        )

        detected = []
        seen_categories = set()

        for sentence in sentences:
            sentence = sentence.strip()

            if not sentence:
                continue

            issue = IssueDetector.normalize_issue(
                raw_text=sentence,
                evidence=sentence,
            )

            if issue.category != IssueCategory.OTHER:
                key = issue.category.value

                if key not in seen_categories:
                    detected.append(issue)
                    seen_categories.add(key)

        return detected