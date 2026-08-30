# Backend fixes applied
- Lazy, resilient Gemini SDK initialization.
- Updated `google-genai` requirement.
- Strict project matching; no cross-project fallback.
- Best match removed from alternatives.
- Proposal overflow now triggers review instead of silently hiding the invalid quantity.
- Low-confidence/no-match activities do not generate proposals.
- Document-level validation included in the audit trail.
- Confidence scoring no longer double-counts semantic/fuzzy/location signals.
- Unit and cumulative quantity consistency checks added.
- Approval endpoint no longer mutates in-memory schedule state.

Run locally: `python -m pip install -r requirements.txt` then `pytest -q`.
