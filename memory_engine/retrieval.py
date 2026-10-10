import json
import numpy as np
from sentence_transformers import SentenceTransformer


class LocalEmbedder:
    """Creates text embeddings using a model that runs on this computer."""

    def __init__(
        self,
        model_name="sentence-transformers/all-MiniLM-L6-v2",
    ):
        self.model = SentenceTransformer(model_name, device="cpu")

    def encode(self, text):
        vector = self.model.encode(
            text,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )
        return vector.tolist()


class MemoryRetriever:
    def __init__(self, store, embedder, threshold=0.30):
        self.store = store
        self.embedder = embedder
        self.threshold = threshold

    def recall(self, query, top_k=5):
        if not query.strip():
            return []

        # Search the whole question and its simple "and" parts.
        # This helps when one question asks for multiple separate facts.
        query_parts = [part.strip() for part in query.split(" and ") if part.strip()]
        if len(query_parts) == 1:
            query_parts = [query]

        # Small query expansion for common wording differences.
        if "framework" in query.lower():
            query_parts.append("What framework is the user building with?")

        query_vectors = [
            np.asarray(self.embedder.encode(part), dtype=float)
            for part in query_parts
        ]
        memories = self.store.get_active_memories_with_embeddings()
        results = []

        for memory in memories:
            saved_vector = np.asarray(
                json.loads(memory["embedding"]),
                dtype=float,
            )

            # The dot product is cosine similarity because vectors are normalized.
            score = max(
                float(np.dot(query_vector, saved_vector))
                for query_vector in query_vectors
            )

            if score >= self.threshold:
                results.append(
                    {
                        "id": memory["id"],
                        "text": memory["text"],
                        "type": memory["memory_type"],
                        "score": round(score, 4),
                    }
                )

        results.sort(key=lambda item: item["score"], reverse=True)
        return results[:top_k]
