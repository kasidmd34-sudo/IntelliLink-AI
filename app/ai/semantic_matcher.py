import logging
from typing import List
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)


class SemanticMatcher:
    """Generates dense semantic embeddings and cosine similarity using SentenceTransformers."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self._model = None

    @property
    def model(self) -> SentenceTransformer:
        if self._model is None:
            logger.info("Loading SentenceTransformer model: %s", self.model_name)
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def compute_similarity(self, query: str, candidate_texts: List[str]) -> List[float]:
        if not query or not candidate_texts:
            return [0.0] * len(candidate_texts)

        query_embedding = self.model.encode(query, convert_to_tensor=True)
        cand_embeddings = self.model.encode(candidate_texts, convert_to_tensor=True)

        from sentence_transformers import util
        cos_scores = util.cos_sim(query_embedding, cand_embeddings)[0].cpu().numpy()
        return [float(max(0.0, min(1.0, score))) for score in cos_scores]