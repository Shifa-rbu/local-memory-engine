from memory_engine.ingestion import extract_memories
from memory_engine.retrieval import LocalEmbedder, MemoryRetriever
from memory_engine.storage import MemoryStore


class MemoryEngine:
    def __init__(self, database_path="data/memories.sqlite3"):
        self.store = MemoryStore(database_path)
        self.embedder = LocalEmbedder()
        self.retriever = MemoryRetriever(self.store, self.embedder)

    def remember(self, message):
        candidates = extract_memories(message)
        saved = []

        for candidate in candidates:
            vector = self.embedder.encode(candidate.text)

            memory_id = self.store.add_memory(
                text=candidate.text,
                memory_type=candidate.memory_type,
                source_message=message,
                slot=candidate.slot,
                embedding=vector,
            )

            saved.append(
                {
                    "id": memory_id,
                    "text": candidate.text,
                    "type": candidate.memory_type,
                }
            )

        return {"saved": saved, "ignored": not bool(saved)}

    def recall(self, query, top_k=5):
        return self.retriever.recall(query, top_k=top_k)
