from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from memory_engine.engine import MemoryEngine


app = FastAPI(
    title="Local Memory Engine",
    description="A local chatbot memory API with semantic recall.",
    version="1.0.0",
)

# The model is loaded once when the API starts.
engine = MemoryEngine("data/memories.sqlite3")


class MemoryRequest(BaseModel):
    message: str | None = None
    text: str | None = None
    memory_type: str = "fact"
    source_message: str | None = None
    slot: str | None = None


class RecallRequest(BaseModel):
    query: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=50)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/memory")
def add_memory(request: MemoryRequest):
    if request.message:
        return engine.remember(request.message)

    if request.text:
        vector = engine.embedder.encode(request.text)
        memory_id = engine.store.add_memory(
            text=request.text,
            memory_type=request.memory_type,
            source_message=request.source_message or request.text,
            slot=request.slot,
            embedding=vector,
        )
        return {
            "saved": [
                {
                    "id": memory_id,
                    "text": request.text,
                    "type": request.memory_type,
                }
            ],
            "ignored": False,
        }

    raise HTTPException(
        status_code=422,
        detail="Provide either 'message' or 'text'.",
    )


@app.post("/recall")
def recall(request: RecallRequest):
    return {
        "memories": engine.recall(
            request.query,
            top_k=request.top_k,
        )
    }


@app.get("/memories")
def list_memories(include_replaced: bool = True):
    return {
        "memories": engine.store.list_memories(
            include_replaced=include_replaced,
        )
    }


@app.delete("/memory/{memory_id}")
def delete_memory(memory_id: int):
    deleted = engine.store.delete_memory(memory_id)

    if not deleted:
        raise HTTPException(status_code=404, detail="Memory not found.")

    return {"deleted": True, "id": memory_id}
