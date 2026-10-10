# Local Memory Engine

A local chatbot memory project for the GDG RBU Machine Learning recruitment task. It extracts selected facts from messages, saves them in SQLite, keeps a history when facts change, and retrieves relevant memories using local text embeddings.

## Setup

Requires Python 3.10 or newer. In PowerShell, from the project folder:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install fastapi "uvicorn[standard]" sentence-transformers numpy pytest httpx

## Run the API

```powershell
python -m uvicorn memory_engine.api:app --reload
