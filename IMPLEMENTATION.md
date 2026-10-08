# IndusConnect - Implementation Details

## Architectural Migration: Scraper & LangGraph to KG-RAG Adzuna Pipeline

The legacy architecture previously relied on an Excel dataset, web scrapers, and a non-deterministic LangGraph ReAct agent. Following the architectural directives in the `IndusConnect_Capstone_Synopsis.docx`, the system has been entirely rebuilt into a deterministic Knowledge-Graph (KG) backed pipeline using Adzuna's job API.

### 1. Ingestion Pipeline (`indusconnect/ingestion.py`)
- **Source**: Jobs are fetched directly from the Adzuna API using an exponential backoff client (`adzuna.py`).
- **Processing**: HTML boilerplates are stripped, and job descriptions are cleaned (`cleaning.py`).
- **Zone Tagging**: Jobs are passed to the Neo4j Knowledge Graph (`kg_resolver.py`), which uses fuzzy matching and alias rules to accurately tag jobs with their specific Pune MIDC Zone (e.g., Hinjewadi, Chakan).
- **Embedding**: The text is embedded using a shared `sentence-transformers/all-MiniLM-L6-v2` singleton (`embedding.py`).
- **Storage**: Jobs and their binary float32 embeddings are stored safely in SQLite using the `AdzunaJob` model (`models_ic.py`).

### 2. FAISS & Retrieval (`indusconnect/retrieval.py`)
- **Index Generation**: Upon startup or after a successful ingestion run, the `AdzunaJob` binary embeddings are read from SQLite and compiled into a FAISS `IndexFlatIP` (cosine similarity) index.
- **Query Resolution**: Search queries undergo KG-resolution first to detect zone and industry intents. 
- **Filtering**: The FAISS index is heavily filtered using the detected MIDC zone for exact deterministic behavior, falling back to pure semantic search if no zone is detected.

### 3. Application Integration (`app.py`)
- The legacy `_build_adzuna_cache()` background threading logic has been completely removed.
- The `api_map_external_jobs` endpoint now queries the SQLite `AdzunaJob` table.
- A new `APScheduler` integration (`indusconnect/scheduler.py`) has been linked to the Flask app context, ensuring the ingestion pipeline runs safely every 24 hours in the background.

## Database
- Reusing the existing SQLite `indusconnect.db`. 
- New Table: `adzuna_job` created natively through `flask-sqlalchemy` without disrupting other existing tables (like `Company`, `Worker`, `TradeRequest`).
