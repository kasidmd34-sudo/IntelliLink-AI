# INTELLILINK AI — Infrastructure Intelligence Layer
*Smart India Hackathon (SIH 2026)*

IntelliLink AI is an AI-powered document intelligence system built for large-scale infrastructure projects. It transforms fragmented progress reports, measurement records, inspection notes, and contractor submissions into structured, auditable schedule update recommendations.

---

## Core Engineering Principles

1. **Human-in-the-Loop Safeguard**: The system produces actionable proposals requiring human sign-off (`requires_human_approval = True`). It never mutates official project records directly.
2. **Hybrid Schedule Matching**: Matches free-form field descriptions to formal WBS tasks using a weighted blend of **Exact**, **Fuzzy (RapidFuzz)**, **Semantic Vector Similarity (SentenceTransformers)**, and **Location Context**.
3. **Multi-Signal Confidence Scoring**: Derives confidence mathematically from extraction completeness, schema compliance, location consistency, and cosine distance.
4. **Controlled Issue Taxonomy**: Normalizes unstructured delay notes into standard categories (`heavy_rainfall`, `labour_shortage`, `material_shortage`, etc.).

---

## Architecture Flow

```text
 Uploaded Document (PDF / Image)
               │
               ▼
 Gemini Multimodal Extraction (Structured JSON)
               │
               ▼
 Strict Pydantic & Business Rule Validation
               │
               ▼
 Hybrid Schedule Matcher (Exact + Fuzzy + Dense Embedding)
               │
               ▼
 Issue Classifier & Non-Destructive Proposal Engine
               │
               ▼
 Frontend Review Screen (Approve / Edit / Reject)



## Technology Stack
AI Model: Gemini 2.5/3.7 Flash via google-genai SDK
Backend Framework: Python 3.11+, FastAPI, Uvicorn (Async)
Validation: Pydantic v2
PDF Preprocessing: PyMuPDF (fitz)
Semantic Similarity: sentence-transformers (all-MiniLM-L6-v2)
Fuzzy Matching: rapidfuzz
Testing & Benchmarks: pytest, scikit-learn, pandas