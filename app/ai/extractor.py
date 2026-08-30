import logging
import re
from typing import Optional

from app.ai.gemini_client import GeminiClient
from app.prompts.extraction_prompt import build_extraction_prompt
from app.schemas.extraction_schema import (
    DocumentExtraction,
    ExtractedActivity,
    SourceEvidence,
)
from app.utils.text_utils import extract_chainage


logger = logging.getLogger(__name__)


class InfrastructureExtractor:
    """
    Coordinates document parsing with Gemini.

    Gemini is the primary extractor.
    A lightweight rule-based fallback is used only if Gemini fails.
    """

    def __init__(self, client: Optional[GeminiClient] = None):
        self.client = client or GeminiClient()

    def extract(
        self,
        file_path: str,
        project_id: Optional[str] = None,
        mime_type: Optional[str] = None,
    ) -> DocumentExtraction:

        prompt = build_extraction_prompt(project_id=project_id)

        try:
            logger.info("Starting Gemini document extraction: %s", file_path)

            raw_json = self.client.generate_structured_extraction(
                prompt=prompt,
                file_path=file_path,
                mime_type=mime_type,
            )

            extraction = DocumentExtraction.model_validate(raw_json)

            if project_id and not extraction.project_id:
                extraction.project_id = project_id

            logger.info(
                "Gemini document extraction succeeded. Activities: %d",
                len(extraction.activities),
            )

            return extraction

        except Exception as e:
            logger.exception("Document extraction failed: %s", str(e))

            return DocumentExtraction(
                project_id=project_id,
                extraction_notes=f"Extraction failed: {str(e)}",
                extraction_status="FAILED",
                activities=[],
            )

    def extract_from_text(
        self,
        text: str,
        project_id: Optional[str] = None,
    ) -> DocumentExtraction:

        prompt = build_extraction_prompt(project_id=project_id)

        if self.client and getattr(self.client, "client", None):
            try:
                logger.info("Using Gemini for text extraction.")

                raw_json = self.client.generate_text_extraction(
                    prompt=prompt,
                    text_content=text,
                )

                extraction = DocumentExtraction.model_validate(raw_json)

                if project_id and not extraction.project_id:
                    extraction.project_id = project_id

                logger.info(
                    "Gemini extraction succeeded. Activities: %d",
                    len(extraction.activities),
                )

                return extraction

            except Exception as e:
                logger.exception(
                    "Gemini text extraction failed. "
                    "Using heuristic fallback. Error: %s",
                    str(e),
                )

        return self._heuristic_text_extraction(
            text=text,
            project_id=project_id,
        )

    def _heuristic_text_extraction(
        self,
        text: str,
        project_id: Optional[str] = None,
    ) -> DocumentExtraction:
        """
        Simple non-recursive fallback extractor.

        This method intentionally does NOT use IssueDetector.
        """

        logger.info("Starting heuristic fallback extraction.")

        known_activities = [
            (
                "Bituminous Road Work",
                [
                    "bituminous",
                    "asphalt",
                    "dbm",
                    "paving",
                    "wearing course",
                ],
            ),
            (
                "Earthwork in Embankment",
                [
                    "earthwork",
                    "embankment",
                    "soil compaction",
                    "earth filling",
                ],
            ),
            (
                "Sub-base Drainage Layer",
                [
                    "sub-base",
                    "sub base",
                    "drainage layer",
                    "gsb",
                    "drainage blanket",
                ],
            ),
            (
                "Site Clearance & Grubbing",
                [
                    "site clearance",
                    "grubbing",
                    "site prep",
                    "land clearing",
                    "land cleared",
                ],
            ),
            (
                "Thermoplastic Road Marking",
                [
                    "thermoplastic",
                    "road marking",
                    "lane marking",
                    "striping",
                ],
            ),
            (
                "Reinforced Concrete Culvert",
                [
                    "culvert",
                    "concrete box culvert",
                    "rcc culvert",
                ],
            ),
        ]

        quantity_pattern = re.compile(
            r"(\d+(?:,\d{3})*(?:\.\d+)?)\s*"
            r"("
            r"square\s+metres?|"
            r"square\s+meters?|"
            r"sq\.?\s*m|"
            r"sqm|"
            r"m2|"
            r"cubic\s+metres?|"
            r"cubic\s+meters?|"
            r"cu\.?\s*m|"
            r"cum|"
            r"m3|"
            r"metres?|"
            r"meters?|"
            r"km|"
            r"nos|"
            r"units?|"
            r"tons?|"
            r"mt"
            r")",
            re.IGNORECASE,
        )

        percentage_pattern = re.compile(
            r"(\d+(?:\.\d+)?)\s*%"
        )

        sentences = re.split(
            r"(?<=[.!?])\s+",
            text.strip(),
        )

        activities = []

        for formal_name, keywords in known_activities:

            relevant_indexes = []

            for index, sentence in enumerate(sentences):
                sentence_lower = sentence.lower()

                if any(
                    keyword in sentence_lower
                    for keyword in keywords
                ):
                    relevant_indexes.append(index)

            if not relevant_indexes:
                continue

            context_indexes = set()

            for index in relevant_indexes:
                context_indexes.add(index)

                if index > 0:
                    context_indexes.add(index - 1)

                if index < len(sentences) - 1:
                    context_indexes.add(index + 1)

            activity_text = " ".join(
                sentences[index]
                for index in sorted(context_indexes)
            )

            quantity_matches = list(
                quantity_pattern.finditer(activity_text)
            )

            quantity_completed = None
            cumulative_quantity = None
            unit = None

            if quantity_matches:
                first_match = quantity_matches[0]

                quantity_completed = float(
                    first_match.group(1).replace(",", "")
                )

                unit = self._normalize_unit(
                    first_match.group(2)
                )

            if len(quantity_matches) > 1:
                second_match = quantity_matches[1]

                cumulative_quantity = float(
                    second_match.group(1).replace(",", "")
                )

            location = (
                extract_chainage(activity_text)
                or extract_chainage(text)
            )

            progress_match = percentage_pattern.search(
                activity_text
            )

            reported_progress_percent = None

            if progress_match:
                reported_progress_percent = float(
                    progress_match.group(1)
                )

            source_evidence = []

            if quantity_completed is not None:
                source_evidence.append(
                    SourceEvidence(
                        field_name="quantity_completed",
                        extracted_value=str(quantity_completed),
                        verbatim_text=activity_text[:500],
                    )
                )

            if cumulative_quantity is not None:
                source_evidence.append(
                    SourceEvidence(
                        field_name="cumulative_quantity",
                        extracted_value=str(cumulative_quantity),
                        verbatim_text=activity_text[:500],
                    )
                )

            if location:
                source_evidence.append(
                    SourceEvidence(
                        field_name="location",
                        extracted_value=location,
                        verbatim_text=activity_text[:500],
                    )
                )

            activities.append(
                ExtractedActivity(
                    activity_name=formal_name,
                    quantity_completed=quantity_completed,
                    cumulative_quantity=cumulative_quantity,
                    unit=unit,
                    location=location,
                    reported_progress_percent=reported_progress_percent,
                    issues=[],
                    source_evidence=source_evidence,
                )
            )

        # Generic fallback only if no known activity was detected.
        if not activities and text.strip():

            location = extract_chainage(text)

            quantity_matches = list(
                quantity_pattern.finditer(text)
            )

            quantity_completed = None
            unit = None

            if quantity_matches:
                quantity_completed = float(
                    quantity_matches[0]
                    .group(1)
                    .replace(",", "")
                )

                unit = self._normalize_unit(
                    quantity_matches[0].group(2)
                )

            evidence = []

            if quantity_completed is not None:
                evidence.append(
                    SourceEvidence(
                        field_name="quantity_completed",
                        extracted_value=str(quantity_completed),
                        verbatim_text=text[:500],
                    )
                )

            activities.append(
                ExtractedActivity(
                    activity_name="Infrastructure Activity",
                    quantity_completed=quantity_completed,
                    unit=unit,
                    location=location,
                    issues=[],
                    source_evidence=evidence,
                )
            )

        logger.info(
            "Heuristic fallback completed. Activities: %d",
            len(activities),
        )

        return DocumentExtraction(
            project_id=project_id or "PROJECT_001",
            project_name="NH-48 Corridor Expansion",
            activities=activities,
            document_level_issues=[],
            extraction_status="SUCCESS",
            extraction_notes=(
                "Rule-based fallback extraction used because "
                "Gemini extraction failed or was unavailable."
            ),
        )

    @staticmethod
    def _normalize_unit(unit: str) -> str:

        normalized = unit.lower().strip()

        normalized = normalized.replace(".", "")
        normalized = re.sub(r"\s+", " ", normalized)

        if normalized in {
            "square metre",
            "square metres",
            "square meter",
            "square meters",
            "sq m",
            "sqm",
            "m2",
        }:
            return "m2"

        if normalized in {
            "cubic metre",
            "cubic metres",
            "cubic meter",
            "cubic meters",
            "cu m",
            "cum",
            "m3",
        }:
            return "m3"

        if normalized in {
            "metre",
            "metres",
            "meter",
            "meters",
        }:
            return "m"

        if normalized in {
            "unit",
            "units",
            "nos",
        }:
            return "nos"

        if normalized in {
            "ton",
            "tons",
            "mt",
        }:
            return "tons"

        return normalized