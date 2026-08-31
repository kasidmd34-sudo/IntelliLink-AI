# IntelliLink AI — Infrastructure Intelligence Layer

**Smart India Hackathon (SIH) 2026**

> **Turning unstructured infrastructure reports into structured, reviewable schedule updates.**

IntelliLink AI is an AI-powered document intelligence system designed for large infrastructure and construction projects.

Infrastructure teams regularly work with progress reports, measurement records, inspection notes, contractor submissions, and other documents that contain important project information in different formats. Reviewing these documents manually and connecting them with the correct project schedule can take significant time and may lead to missed or inconsistent updates.

**IntelliLink AI helps automate this process.**

It reads project documents, extracts relevant information, identifies the most likely matching schedule activity, classifies reported issues, and creates a **reviewable schedule update proposal** for the project team.

The system does **not** directly change official project records. Every proposed update can be reviewed, edited, approved, or rejected by a human.

---

## What IntelliLink AI Does

The system follows a simple workflow:

1. **Upload** a project document such as a PDF or image.
2. **Extract** important project information using Gemini's multimodal capabilities.
3. **Validate** the extracted information against defined schemas and business rules.
4. **Match** the reported work with the correct WBS/schedule activity.
5. **Identify** issues such as rainfall, labour shortages, or material shortages.
6. **Generate** a proposed schedule update.
7. **Review** the proposal through the frontend.
8. **Approve, edit, or reject** the proposed update.

---

## Core Engineering Principles

### 1. Human-in-the-Loop

AI recommendations are treated as **proposals, not final decisions**.

Every generated update contains:

```python
requires_human_approval = True
```

The system never directly modifies official project records. A project team member must review and approve the recommendation before it can be applied.

---

### 2. Hybrid Schedule Matching

Field reports rarely use the exact same wording as the official project schedule.

For example:

```text
Field Report:
"Concrete work completed near the east side of the bridge."

Schedule:
"Pier P4 — RCC Concrete Work"
```

To handle these differences, IntelliLink AI combines multiple matching methods:

* **Exact matching** — Finds direct name matches.
* **Fuzzy matching** — Handles spelling and wording differences using RapidFuzz.
* **Semantic similarity** — Understands meaning using SentenceTransformers.
* **Location context** — Uses project/location information to improve the match.

Using multiple signals makes the matching process more reliable than depending on a single method.

---

### 3. Multi-Signal Confidence Scoring

The system does not rely only on the AI model's response.

A confidence score is calculated using multiple signals, including:

* Extraction completeness
* Schema validation
* Location consistency
* Schedule matching score
* Semantic similarity
* Overall data quality

This helps the system identify stronger and weaker recommendations and allows the reviewer to make a more informed decision.

---

### 4. Controlled Issue Classification

Delay and progress reports often contain different descriptions for the same type of problem.

For example:

```text
"Continuous rain stopped excavation work."
```

can be normalized to:

```text
heavy_rainfall
```

The system uses a controlled set of issue categories such as:

```text
heavy_rainfall
labour_shortage
material_shortage
equipment_failure
site_access_issue
approval_delay
```

This makes project issues easier to track, filter, and analyze.

---

## System Architecture

```text
                    ┌─────────────────────────┐
                    │   Project Document      │
                    │    PDF / Image / Report │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │  Gemini Multimodal AI   │
                    │   Structured Extraction │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Pydantic + Business     │
                    │ Rule Validation         │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Hybrid Schedule Matcher │
                    │ Exact + Fuzzy + Semantic│
                    │ + Location              │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │ Issue Classification &  │
                    │ Proposal Generation     │
                    └────────────┬────────────┘
                                 │
                                 ▼
                    ┌─────────────────────────┐
                    │     Review Interface    │
                    │                         │
                    │   ✓ Approve             │
                    │   ✎ Edit                │
                    │   ✕ Reject              │
                    └─────────────────────────┘
```

---

## Technology Stack

| Component                        | Technology                      |
| -------------------------------- | ------------------------------- |
| **AI / Document Understanding**  | Gemini Flash via `google-genai` |
| **Backend**                      | Python 3.11+, FastAPI           |
| **Server**                       | Uvicorn                         |
| **Data Validation**              | Pydantic v2                     |
| **PDF Processing**               | PyMuPDF (`fitz`)                |
| **Semantic Matching**            | SentenceTransformers            |
| **Embedding Model**              | `all-MiniLM-L6-v2`              |
| **Fuzzy Matching**               | RapidFuzz                       |
| **Testing**                      | pytest                          |
| **Data Analysis / Benchmarking** | pandas, scikit-learn            |

---

## Why Hybrid Matching?

A construction schedule contains formal activity names, while field reports are usually written in natural language.

A single matching technique can therefore produce unreliable results.

IntelliLink AI combines:

```text
Exact Match
     +
Fuzzy Match
     +
Semantic Similarity
     +
Location Context
     ↓
Final Schedule Match
     ↓
Confidence Score
```

This approach allows the system to handle both simple matches and reports where the wording is significantly different from the schedule.

---

## Safety & Reliability

IntelliLink AI is designed around **controlled automation**.

The system follows these rules:

* AI output is validated before being used.
* Invalid or incomplete data is rejected.
* Schedule updates are generated as proposals.
* Official records are not changed automatically.
* Human approval is required before applying a recommendation.
* Matching results include confidence information.
* Issues are mapped to controlled categories instead of relying only on free-form text.

The goal is not to replace the project engineer or manager.

**The goal is to reduce repetitive document review while keeping the final decision with the project team.**

---

## Example

### Input

A contractor submits a progress report containing:

```text
"Due to continuous heavy rainfall, excavation work
at the east side of the bridge could not continue.
Approximately 70% of the planned excavation has
been completed."
```

### IntelliLink AI Extracts

```json
{
  "activity": "Excavation Work",
  "location": "East Side of Bridge",
  "progress": 70,
  "issue": "heavy_rainfall"
}
```

### Schedule Matching

The system searches the project's WBS activities and compares the extracted activity using:

```text
Exact Match
Fuzzy Match
Semantic Similarity
Location
```

### Output

Instead of directly changing the project schedule, the system creates a proposal:

```text
Matched Activity:
Bridge East Side — Excavation Work

Reported Progress:
70%

Issue:
Heavy Rainfall

Action:
Schedule Update Recommended

Human Approval:
Required
```

The project team can then **Approve, Edit, or Reject** the recommendation.

---

## Project Objective

IntelliLink AI aims to make infrastructure project reporting:

**Faster → More Consistent → Easier to Review → Safer to Automate**

By combining document understanding, schedule matching, structured validation, and human review, the system provides a practical way to connect unstructured project documents with formal project schedules.

---

## Project Status

**Built for:** Smart India Hackathon 2026
**Project:** IntelliLink AI
**Focus:** Infrastructure Document Intelligence & Schedule Assistance

---
