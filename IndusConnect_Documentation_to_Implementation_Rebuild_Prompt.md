# IndusConnect — Documentation-to-Implementation Rebuild Prompt

## Purpose

Rebuild the existing IndusConnect implementation so that the **actual code execution matches the architecture described in the project synopsis**.

Project:

**IndusConnect: Smart Job Matching for MIDC Industrial Workers**

The project synopsis is the architectural source of truth. The existing implementation should be inspected and then replaced where it conflicts with the documented design.

> **Documentation = target architecture.**
>
> **Code = actual execution.**
>
> The goal is to make the code genuinely execute the documented architecture, not merely rewrite documentation to make the existing code appear compliant.

---

# 1. Source of Truth

Use the uploaded:

`IndusConnect_Capstone_Synopsis(1).docx`

as the primary architectural specification.

The documented pipeline is:

```text
Worker Signup
    ↓
Plain-language Skills & Experience
    ↓
Worker Profile Embedding
    ↓
Daily Job Collection
    ↓
Cleaning
    ↓
Knowledge Graph Zone Tagging
    ↓
Job Embedding
    ↓
Worker Query
    ↓
Knowledge Graph Zone Detection
    ↓
Zone Filtering
    ↓
RAG Semantic Ranking
    ↓
Cosine Similarity
    ↓
Ranked Job Results
```

The implementation must actually follow this sequence.

---

# 2. Inspect Before Removing Anything

The existing implementation is not the target architecture.

First inspect the complete repository and identify:

- old RAG implementation
- old Excel-based indexing pipeline
- old FAISS company-record indexing
- old ReAct-agent-first architecture
- obsolete mock job data
- obsolete hardcoded company data
- obsolete retrieval functions
- duplicate pipelines
- unused job-search tools
- old fallback logic

Do **not** blindly delete configuration, frontend, authentication, database schemas, or reusable infrastructure.

Before deleting or replacing code:

1. inspect the repository
2. identify dependencies
3. identify frontend/backend contracts
4. identify reusable Neo4j logic
5. identify reusable database configuration
6. identify existing API routes
7. create a migration/replacement plan

Then remove or replace the old implementation where necessary.

The final system must have **one clear primary job-matching pipeline**.

---

# 3. Final Target Architecture

Implement:

```text
                    ┌─────────────────────────┐
                    │      Worker Signup      │
                    │ Skills + Experience     │
                    │    Plain Language       │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Worker Profile Embedding│
                    └────────────┬────────────┘
                                 │
                                 │
External Adzuna API ──→ Job Ingestion
                                 ↓
                    ┌─────────────────────────┐
                    │ Job Cleaning / Parsing  │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Knowledge Graph Tagging │
                    │ Company → Zone →        │
                    │ Industry                │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Job Embedding           │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Job Vector Store        │
                    └────────────┬────────────┘
                                 │
                         Worker Query
                                 ↓
                    ┌─────────────────────────┐
                    │ Query / Zone Detection  │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ KG Zone Filter          │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Semantic Retrieval      │
                    │ + Cosine Similarity     │
                    └────────────┬────────────┘
                                 ↓
                    ┌─────────────────────────┐
                    │ Ranked Job Results      │
                    └─────────────────────────┘
```

---

# 4. Replace the Old RAG as the Primary Job Retrieval System

The old Excel/company-record RAG must **not** remain the primary job retrieval source.

The primary vector index must represent:

**actual job listings obtained from Adzuna**

rather than:

**static Excel company records**.

The Excel dataset may remain only if genuinely required for supporting Knowledge Graph data.

---

# 5. Adzuna API Is the Job Source

Daily job ingestion must use the **Adzuna API**.

Do not use:

- fake job JSON
- hardcoded jobs
- static mock jobs
- the old Excel dataset as the primary job source
- manually created job advertisements

Use the real Adzuna REST API.

Base API:

```text
https://api.adzuna.com/v1/api
```

Search requests use the Adzuna jobs search API and require:

- `app_id`
- `app_key`

Use environment variables.

Example:

```env
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
ADZUNA_COUNTRY=in
```

Never hardcode API credentials.

---

# 6. Inspect the Real Adzuna API Response First

Before implementing the normalization layer, make a real Adzuna API request using the configured credentials.

Do **not** invent the response schema.

During development, inspect a sanitized sample response and identify:

- top-level keys
- `results`
- job ID
- title
- description
- company
- location
- category
- contract type
- contract time
- salary fields
- created timestamp
- redirect URL
- latitude
- longitude
- additional fields

The search response commonly contains a `results` array and fields such as:

- `id`
- `title`
- `description`
- `company.display_name`
- `location.display_name`
- `location.area`
- `category.label`
- `category.tag`
- `contract_type`
- `contract_time`
- `salary_min`
- `salary_max`
- `salary_is_predicted`
- `created`
- `redirect_url`
- `latitude`
- `longitude`

However, code defensively.

Fields can be missing or null.

Never assume every job has salary, category, coordinates, company information, or contract information.

If the actual API response differs, adapt the code to the **actual response** and document the observed schema.

---

# 7. Canonical Job Model

Create a normalized internal Job model.

Recommended fields:

```text
id
source
source_job_id
title
description
company_name
location_display
location_area
latitude
longitude
category_label
category_tag
contract_type
contract_time
salary_min
salary_max
salary_is_predicted
created_at
redirect_url
midc_zone
industry
raw_source_data
last_seen_at
active
```

Preserve source information.

Do not lose the original Adzuna job ID or redirect URL.

Keep raw source data where appropriate for debugging/auditing.

---

# 8. Daily Job Ingestion

Implement:

```text
Adzuna API
    ↓
Fetch jobs
    ↓
Pagination
    ↓
Deduplication
    ↓
Normalization
    ↓
Cleaning
    ↓
MIDC zone resolution
    ↓
Industry resolution
    ↓
Persistence
    ↓
Job embeddings
    ↓
Vector index update
```

The documented system expects a **24-hour refresh**.

Provide:

1. manual ingestion command for development/testing
2. scheduled ingestion
3. configurable refresh interval

---

# 9. Pagination

Adzuna search is page-based.

Implement safe pagination.

Configuration:

```env
ADZUNA_RESULTS_PER_PAGE=
ADZUNA_MAX_PAGES=
```

Stop when:

- no results are returned
- maximum configured pages are reached
- the API indicates no more results

Never create an infinite loop.

---

# 10. Rate Limiting and Retries

Implement:

- request timeout
- retries
- exponential backoff
- HTTP error handling
- rate-limit handling
- structured logging
- partial-ingestion recovery

One failed page must not crash the entire ingestion process.

Log:

- page number
- jobs received
- jobs normalized
- jobs discarded
- jobs zone-tagged
- jobs embedded

---

# 11. Job Cleaning

The synopsis requires job cleaning.

Implement cleaning that:

- removes obvious contact boilerplate
- removes duplicated whitespace
- removes HTML where appropriate
- normalizes text
- removes irrelevant repeated text
- preserves meaningful job skills
- preserves title
- preserves experience requirements
- preserves location
- preserves company
- preserves responsibilities

Do not aggressively remove skill information.

The cleaned text must remain useful for semantic embeddings.

---

# 12. Knowledge Graph

Use Neo4j for structured location and industry relationships.

Core relationship:

```text
Company
   ↓ LOCATED_IN
MIDCZone
   ↓
Industry
```

Use the documented set of MIDC zones.

The Knowledge Graph should answer:

> "Which MIDC zone does this company/job belong to?"

The KG should be responsible for exact/structured location resolution.

Do not use embeddings as the authoritative method for assigning the final MIDC zone when an exact KG mapping exists.

---

# 13. Job Zone Tagging

For every ingested job:

1. obtain company
2. obtain location
3. normalize location
4. resolve against Neo4j
5. assign MIDC zone
6. assign industry where available

Conceptually:

```text
Job
 ↓
Company + Location
 ↓
Neo4j
 ↓
Company → MIDCZone → Industry
 ↓
midc_zone
industry
```

If the zone cannot be confidently resolved:

```text
midc_zone = null
```

Never fabricate a zone.

---

# 14. Location Resolution

Support common variants such as:

```text
Chakan
Chakan MIDC
Chakan Industrial Area

Bhosari
Bhosari MIDC

Pimpri
Talegaon
Ranjangaon
Hinjewadi
```

The final canonical zone must come from the configured Knowledge Graph mappings.

Do not invent new zones.

---

# 15. Worker Signup

Worker signup must allow:

- skills
- experience
- optional preferred location
- optional preferred industry
- optional language

The worker must be able to describe experience in natural language.

Example:

```text
I have 4 years experience as a CNC operator.
I can operate CNC turning machines and do basic machine maintenance.
I want work around Chakan.
```

Do not require an ATS-style resume.

---

# 16. Worker Profile Embedding

Convert the worker's plain-language profile into an embedding.

Use the **same embedding model** for:

- worker profile
- job listings
- search queries

The current project analysis identified:

```text
sentence-transformers/all-MiniLM-L6-v2
```

as the embedding model.

If retaining it:

- dimension = 384
- normalize vectors
- use cosine similarity consistently

Persist worker embeddings appropriately.

---

# 17. Job Embedding

Construct embedding text from meaningful job information.

Example:

```text
Title:
CNC Machine Operator

Company:
ABC Engineering

Description:
CNC turning, machine operation, production and basic maintenance.

Industry:
Manufacturing

Location:
Chakan MIDC

Contract:
Full-time
```

Then:

```text
SentenceTransformer
      ↓
384-dimensional vector
      ↓
L2 normalization
      ↓
FAISS
```

Do not embed irrelevant raw metadata.

---

# 18. Vector Store

Use FAISS unless there is a concrete project requirement for another vector database.

If using:

```python
faiss.IndexFlatIP(dim)
```

then normalize both:

- stored job vectors
- query/worker vectors

so inner product corresponds to cosine similarity.

The implementation must be explicit and consistent about this.

---

# 19. Vector-to-Job Mapping

The implementation must guarantee:

```text
FAISS vector
     ↕
Job record
```

Never rely on an unvalidated fragile positional array.

If using IDs, maintain a reliable mapping from vector IDs to database job IDs.

When jobs are updated/deactivated, ensure the vector index and database remain consistent.

---

# 20. Worker Query

Example:

```text
Mujhe Chakan MIDC mein welding ki job chahiye.
```

The system should identify:

```text
zone = Chakan
skill/query = welding
```

Then execute:

```text
Query
 ↓
Zone resolution
 ↓
Knowledge Graph
 ↓
Chakan candidate jobs
 ↓
Semantic ranking
 ↓
Top matching jobs
```

---

# 21. KG-FIRST RETRIEVAL

This is mandatory.

If the query contains a recognized MIDC zone:

```text
User Query
    ↓
Zone Detection
    ↓
Neo4j
    ↓
Jobs in that zone
    ↓
Semantic retrieval
    ↓
Ranking
```

Do **not** perform global vector retrieval first and filter afterward.

The documented architecture is KG-first.

---

# 22. No-Zone Query

If the user asks:

```text
I need a welding job.
```

and no MIDC zone is recognized:

```text
Query
 ↓
Query embedding
 ↓
Full active job vector index
 ↓
Cosine similarity
 ↓
Rank
 ↓
Top-K jobs
```

Do not invent a location.

---

# 23. Code-Mixed Queries

Support examples:

```text
Mujhe Chakan MIDC me job chahiye

Chakan mein welding ka kaam hai kya?

mala Bhosari MIDC madhe job pahije

I need CNC operator job in Chakan MIDC
```

Normalize recognized zone expressions to the canonical Knowledge Graph zone.

---

# 24. Semantic Matching

Matching must be semantic rather than exact keyword matching.

Example:

```text
Worker:
welding

Job:
fabrication / arc welding
```

Another:

```text
Worker:
CNC operator

Job:
CNC machine operator / CNC turning
```

Use embeddings and cosine similarity.

Do not implement semantic matching as simple string equality.

---

# 25. Ranking

For each candidate:

```text
similarity =
    cosine(query_or_worker_embedding, job_embedding)
```

Sort descending.

Return Top-K.

Store similarity internally.

Do not display arbitrary percentages such as "95% match" unless a clear mathematical interpretation is defined.

---

# 26. RAG Generation

After retrieval:

```text
Retrieved Jobs
      ↓
Grounded Context
      ↓
Gemini
      ↓
Natural-language response
```

The generation prompt must:

- use only retrieved job information
- not invent companies
- not invent salaries
- not invent locations
- not invent descriptions
- preserve source information
- clearly state when information is unavailable

Keep the distinction:

```text
Neo4j  = structured location/relationship layer
FAISS  = semantic retrieval layer
Gemini = generation layer
```

---

# 27. Source Attribution

Every job result should preserve:

- Adzuna job ID
- company
- title
- location
- created date where available
- source = Adzuna
- redirect URL

Never fabricate source URLs.

The user should be able to follow the original listing through the stored Adzuna redirect URL where permitted.

---

# 28. Adzuna Description Handling

Do not assume the search response description is the complete job description.

Store the description exactly as received.

Use it for semantic retrieval.

Do not claim that it contains information that was not returned.

If additional Adzuna endpoints are needed, inspect the official documentation before implementing them.

Never invent unsupported endpoints.

---

# 29. Database

Recommended conceptual schema:

## Worker

```text
id
profile_text
embedding
preferred_zone
preferred_industry
created_at
updated_at
```

## Job

```text
id
source
source_job_id
title
description
company_name
location
midc_zone
industry
category
contract_type
contract_time
salary_min
salary_max
created_at
redirect_url
raw_data
embedding
last_seen_at
active
```

Never store API keys in the database.

---

# 30. Daily Refresh

Every 24 hours:

1. call Adzuna
2. retrieve current listings
3. normalize
4. clean
5. resolve KG zone
6. update job records
7. create/update embeddings
8. update vector index
9. mark stale jobs inactive if appropriate
10. log ingestion statistics

Do not create duplicates every day.

Use Adzuna's job ID as the source identifier where available.

---

# 31. Remove ReAct-Agent-First Architecture

Do not make the old LangGraph ReAct agent the core matching mechanism.

The core pipeline must be deterministic:

```text
KG filtering
     ↓
Semantic retrieval/ranking
```

If Gemini is used, use it for:

- natural-language response generation
- optional query interpretation

Do not allow an agent to arbitrarily decide whether to use KG or RAG.

---

# 32. Required Backend APIs

Implement clean endpoints such as:

```text
POST /api/workers
```

Create worker profile.

```text
POST /api/workers/{worker_id}/query
```

Match jobs for worker/query.

```text
POST /api/jobs/ingest
```

Manually trigger Adzuna ingestion.

```text
GET /api/jobs
```

Browse active jobs.

```text
GET /api/jobs/{job_id}
```

Get job details.

```text
POST /api/jobs/reindex
```

Rebuild vector index.

```text
GET /api/health
```

Health check.

Follow existing project API conventions where appropriate.

---

# 33. Manual Ingestion Command

Provide a development command such as:

```bash
python -m app.ingestion.run
```

or an equivalent command appropriate to the repository.

It should execute:

```text
Adzuna
→ normalize
→ clean
→ KG
→ persist
→ embed
→ index
```

Print statistics such as:

```text
==================================================
INDUSCONNECT JOB INGESTION
==================================================
Source: Adzuna
Pages fetched: 5
Jobs received: 500
Jobs normalized: 492
Jobs cleaned: 492
Jobs zone-tagged: 421
Jobs without zone: 71
New jobs: 120
Updated jobs: 372
Embeddings generated: 492
Vector index size: 492
==================================================
```

---

# 34. Scheduling

Implement a real 24-hour refresh mechanism.

The exact scheduler may depend on the project's deployment environment.

Support:

- local scheduled execution for development
- production scheduler where appropriate

The architecture should not require a developer to manually run ingestion every day.

---

# 35. Testing

Create tests for:

## Adzuna

- successful API response
- missing fields
- API failure
- pagination
- duplicate jobs
- rate limiting

## Cleaning

- HTML
- boilerplate
- whitespace
- empty description

## Knowledge Graph

- Chakan
- Bhosari
- unknown location

## Embeddings

- same model for worker/job/query
- vector dimension
- normalization

## Retrieval

- zone-filtered retrieval
- global retrieval
- cosine ranking
- top-K
- similarity threshold

## Worker Matching

Example:

```text
Worker:
CNC operator with 3 years experience

Query:
I need CNC operator work in Chakan

Expected:
Chakan jobs are considered first.
```

## Code-Mixed Query

```text
Mujhe Chakan MIDC me welding ki job chahiye
```

Expected:

```text
Zone = Chakan
Semantic query = welding
```

---

# 36. End-to-End Test

Create an end-to-end test that executes:

```text
1. Fetch Adzuna jobs
2. Normalize
3. Clean
4. Resolve zones using Neo4j
5. Embed jobs
6. Build/update FAISS
7. Create worker profile
8. Embed worker profile
9. Submit worker query
10. Detect zone
11. Filter through KG
12. Perform semantic ranking
13. Generate grounded response
14. Return ranked jobs + source URLs
```

The test must prove that the documented architecture actually executes.

---

# 37. Logging

Add structured logging:

```text
[ADZUNA]
[INGESTION]
[CLEANING]
[KG]
[EMBEDDING]
[VECTOR]
[QUERY]
[RETRIEVAL]
[GENERATION]
```

Example:

```text
[ADZUNA] fetched 100 jobs
[KG] resolved 84 jobs to MIDC zones
[EMBEDDING] generated 100 vectors
[VECTOR] index contains 100 jobs
[QUERY] detected zone=Chakan
[KG] filtered candidates=37
[RETRIEVAL] ranked 37 candidates
[GENERATION] context jobs=5
```

This is important for demonstration and viva.

---

# 38. Error Handling

If Adzuna fails:

```text
Keep existing active jobs.
```

If Neo4j fails:

```text
Do not invent zones.
Log the failure.
```

If embedding fails:

```text
Do not insert incomplete vector records.
```

If FAISS fails:

```text
Return a meaningful retrieval error.
```

If Gemini fails:

```text
Still return ranked job cards if retrieval succeeded.
```

If no jobs match:

```text
Return an honest no-match response.
```

Never fabricate results.

---

# 39. Environment Variables

Use `.env`.

Example:

```env
ADZUNA_APP_ID=
ADZUNA_APP_KEY=
ADZUNA_COUNTRY=in

NEO4J_URI=
NEO4J_USERNAME=
NEO4J_PASSWORD=

GEMINI_API_KEY=

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2

TOP_K=10
SIMILARITY_THRESHOLD=0.25

INGESTION_INTERVAL_HOURS=24
ADZUNA_RESULTS_PER_PAGE=50
ADZUNA_MAX_PAGES=5
```

Create:

```text
.env.example
```

Never commit `.env`.

---

# 40. Do Not Overengineer

Do not introduce unnecessary:

- microservices
- agents
- vector databases
- LLM calls
- orchestration layers

Keep the core architecture:

```text
Adzuna
   ↓
Cleaning
   ↓
Neo4j zone tagging
   ↓
Job embeddings
   ↓
FAISS
   ↓
KG-first query filtering
   ↓
Semantic ranking
   ↓
Gemini response
```

---

# 41. Required Implementation Documentation

After implementation create:

```text
IMPLEMENTATION.md
```

It must describe the **actual implementation**, not planned features.

Include:

1. Architecture
2. Repository structure
3. Adzuna integration
4. Actual Adzuna response schema observed
5. Job normalization
6. Cleaning
7. Knowledge Graph
8. Job embedding
9. Worker embedding
10. FAISS
11. Query flow
12. KG-first filtering
13. Semantic ranking
14. Gemini generation
15. Daily ingestion
16. Database schema
17. API endpoints
18. Environment variables
19. Test commands
20. End-to-end execution
21. Known limitations

Never document a feature as implemented unless it has actually been tested.

---

# 42. Final Validation Checklist

Before declaring completion:

- [ ] Old Excel RAG removed from primary job retrieval
- [ ] Actual Adzuna API used
- [ ] Real Adzuna response inspected
- [ ] Actual response schema documented
- [ ] Jobs normalized
- [ ] Jobs cleaned
- [ ] Jobs zone-tagged using Neo4j
- [ ] Jobs receive embeddings
- [ ] Worker receives embedding
- [ ] Same embedding model used
- [ ] FAISS contains job vectors
- [ ] Query zone resolved using KG
- [ ] KG filtering happens BEFORE semantic ranking
- [ ] Semantic ranking uses cosine similarity
- [ ] Top-K jobs returned
- [ ] Gemini receives retrieved context
- [ ] Adzuna source URLs preserved
- [ ] Daily ingestion exists
- [ ] Duplicate jobs handled
- [ ] API failures handled
- [ ] No fake job data
- [ ] No hardcoded API credentials
- [ ] Tests exist
- [ ] End-to-end test executed
- [ ] IMPLEMENTATION.md matches actual code

---

# 43. Evidence-Based Completion

Do not claim the architecture is implemented merely because files or functions exist.

Run the system.

For every major component provide:

```text
FILE
→ FUNCTION
→ INPUT
→ PROCESSING
→ OUTPUT
```

Example:

```text
Adzuna API
→ fetch_jobs()
→ raw API JSON
→ normalized Job objects
→ list[Job]

Job Embedding
→ embed_jobs()
→ cleaned Job objects
→ SentenceTransformer
→ normalized vectors

Knowledge Graph
→ resolve_job_zone()
→ company/location
→ Neo4j query
→ MIDC zone

Retrieval
→ search_jobs()
→ query embedding + zone
→ KG filtering + FAISS
→ ranked jobs

Generation
→ generate_response()
→ retrieved jobs
→ Gemini
→ grounded response
```

---

# 44. Final Report

When implementation is complete, report:

1. What old components were removed
2. What was newly implemented
3. Adzuna API endpoint used
4. Actual response fields observed
5. Job normalization schema
6. Knowledge Graph flow
7. Embedding model
8. Vector index
9. Query execution flow
10. Daily ingestion mechanism
11. Files changed
12. Tests executed
13. Example end-to-end query
14. Remaining gaps between synopsis and implementation

If any requirement cannot be implemented because credentials, code, data, or external access is missing, clearly identify the gap.

Do not pretend it works.

The final implementation must be demonstrable locally.
