import re


def normalize_text(text: str) -> str:
    """
    Normalize text for matching and comparison.
    Converts text to lowercase, removes extra spaces,
    and collapses whitespace.
    """
    if not text:
        return ""

    text = text.lower()
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def extract_chainage(text: str) -> str | None:
    """
    Extract road chainage/location such as:
    Km 12
    Km 12-18
    Km 12 to Km 18
    between Km 12 and Km 18
    """

    if not text:
        return None

    patterns = [
        # Km 12-18
        r"\bkm\.?\s*(\d+(?:\.\d+)?)\s*[-–]\s*(\d+(?:\.\d+)?)\b",

        # Km 12 to Km 18
        r"\bkm\.?\s*(\d+(?:\.\d+)?)\s+to\s+km\.?\s*(\d+(?:\.\d+)?)\b",

        # between Km 12 and Km 18
        r"\bbetween\s+km\.?\s*(\d+(?:\.\d+)?)\s+and\s+km\.?\s*(\d+(?:\.\d+)?)\b",

        # Km 12
        r"\bkm\.?\s*(\d+(?:\.\d+)?)\b",
    ]

    for index, pattern in enumerate(patterns):
        match = re.search(pattern, text, re.IGNORECASE)

        if match:
            if index in [0, 1, 2]:
                start = match.group(1)
                end = match.group(2)
                return f"Km {start}-{end}"

            return f"Km {match.group(1)}"

    return None