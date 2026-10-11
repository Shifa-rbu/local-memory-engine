# Local Memory Engine

A local chatbot memory engine for the GDG RBU 2026–27 Machine Learning recruitment task. It extracts selected facts from conversation messages, saves them in SQLite, keeps a history when facts change, and retrieves relevant memories using local text embeddings.

## Features

- Extracts supported facts, preferences, project details, deadlines, and goals from messages.
- Ignores common small-talk messages such as “ok thanks.”
- Saves each memory’s type, timestamp, source message, and embedding.
- Keeps replaced memories in the database and marks the newer memory as current.
- Uses a local Sentence Transformers model to retrieve relevant memories.
- Returns an empty list when no memory passes the relevance threshold.
- Provides API routes to add, recall, list, and delete memories.

## Requirements

- Python 3.10 or newer.
- Internet access for the first download of `sentence-transformers/all-MiniLM-L6-v2` (about 90 MB).
- After the initial download, the embedding model runs locally on CPU.
- The core features do not use a paid API.

## Setup

Open PowerShell in the project folder and run:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

If PowerShell blocks virtual-environment activation, run this in the same terminal and retry activation:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Run the API

From the project folder, with the virtual environment activated:

```powershell
python -m uvicorn memory_engine.api:app --reload
```

The API runs at `http://127.0.0.1:8000`. Open `http://127.0.0.1:8000/docs` for interactive API documentation.

The SQLite database is stored locally at `data/memories.sqlite3`.

## API routes

- `GET /health` — check that the API is running.
- `POST /memory` — add a message or directly specified memory.
- `POST /recall` — search for relevant memories.
- `GET /memories` — list memories, including replaced memories by default.
- `DELETE /memory/{memory_id}` — delete a memory by ID.

### Add a memory

Send this JSON body to `POST /memory`:

```json
{
  "message": "I use Arch Linux."
}
```

PowerShell example:

```powershell
Invoke-RestMethod `
  -Method Post `
  -Uri "http://127.0.0.1:8000/memory" `
  -ContentType "application/json" `
  -Body (@{ message = "I use Arch Linux." } | ConvertTo-Json )
```

### Recall a memory

Send this JSON body to `POST /recall`:

```json
{
  "query": "What operating system does the user use?",
  "top_k": 5
}
```

The response includes matching memories and their relevance scores. If no memory is relevant enough, the `memories` list is empty.

## Architecture

```text
Conversation message
        |
        v
ingestion.py — extracts supported memory candidates
        |
        v
engine.py — coordinates memory operations
        |
        +------> local Sentence Transformers model
        |         creates embeddings
        |
        +------> storage.py — SQLite records and update history
        |
        +------> retrieval.py — similarity scoring and ranking
        |
        v
api.py — FastAPI endpoints
```

The modules have separate responsibilities:

- `ingestion.py` contains the rules that decide which supported messages become memories.
- `storage.py` saves memories and replacement history in SQLite.
- `retrieval.py` compares query and memory embeddings and ranks active records.
- `engine.py` connects ingestion, embeddings, storage, and recall.
- `api.py` exposes the features through HTTP endpoints.

## Design decisions

SQLite keeps the project simple to run locally without setting up a separate database server. Sentence Transformers provides semantic embeddings without sending conversation text to a paid API. The memory extraction and update logic is implemented in this project rather than delegated to an existing memory library.

The extractor recognizes a limited set of message patterns. When a new memory uses the same slot as an existing active memory, the older record is marked `replaced` and points to the newer record. The old record remains in history, while recall searches active memories.

Recall uses cosine similarity and a threshold of `0.30`. A small query expansion handles some questions containing the word “framework.” These are heuristics, not guarantees. If no active memory meets the threshold, recall returns no results rather than inventing an answer.

## Evaluation

Run the evaluation script from the project folder:

```powershell
python evaluate.py
```

The observed run reported **31/31 cases passed (100%)**. The hand-written cases cover supported facts, preferences, projects, deadline updates, queries for multiple memories, small talk, and questions whose answers are not stored.

This is a small test set, not proof of perfect performance on unseen conversations. The framework query expansion was added after inspecting failures in this same test set, so the result applies to these cases only.

## Limitations and future work

- The extractor supports a limited set of message patterns and may miss other natural phrasings.
- Memories are not separated by user account.
- The local API has no authentication and is intended for use on the developer’s computer.
- Recall compares the query with active memories one at a time. This would become slow with very large collections. A vector index such as FAISS or sqlite-vec could be explored later.
- The relevance threshold and query expansion need testing on a larger, independently written test set.
With 10 million memories, the first bottleneck would be retrieval latency. The current implementation compares the query with every active memory one by one. I would use an approximate-nearest-neighbor index such as FAISS or sqlite-vec to find candidate memories faster, while keeping SQLite for memory text and metadata. I would benchmark retrieval speed and result quality before choosing an index. This project does not currently implement or benchmark that solution.

## Privacy

Memory text, source messages, timestamps, and embeddings are stored in the local SQLite database under `data/`. Keep this database private. The embedding model runs locally after its initial download. Do not expose the unauthenticated development API to the public internet.

## Video walkthrough checklist

Record a 5–10 minute walkthrough covering:

1. The architecture and why SQLite and local embeddings were chosen.
2. Adding a message and showing its saved memory.
3. Updating a deadline and showing the old memory marked as replaced.
4. Recalling a known answer and an unknown answer.
5. Running `python evaluate.py` and showing the result.
6. Limitations and what you would improve next.

## AI assistance disclosure

I used an AI coding assistant to scaffold and revise parts of the Python modules and to help diagnose errors. I ran the application and evaluation locally, checked the API and update behavior, and reviewed the results. I am continuing to study the implementation so I can explain its design, trade-offs, and limitations. The initial code was substantially AI-assisted; I will describe my own changes and understanding honestly.
