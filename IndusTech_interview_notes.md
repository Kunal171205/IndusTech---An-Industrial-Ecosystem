# ═══════════════════════════════════════

# DOCUMENT 1: INTERVIEW NOTES V1

# ═══════════════════════════════════════

## 1. TECH STACK AUDIT

- **Python / Flask (app.py)**: Core web backend framework. Used to quickly build a monolith orchestrator integrating multiple AI/DB libraries.
- **SQLAlchemy (models.py)**: ORM for SQLite/PostgreSQL. Used to securely manage relational state (Users, Jobs).
- **FAISS (faiss-cpu)**: Vector database. Used for blazing-fast, in-memory semantic similarity search across 6,002 company profiles.
- **SentenceTransformers (all-MiniLM-L6-v2)**: Embedding model. Used locally to turn natural language queries into 384-dimensional vectors without API costs.
- **Neo4j**: Graph Database. Used to query structural, topological relationships between Companies, Industries, and MIDC Zones (Knowledge Graph).
- **LangChain / LangGraph**: LLM orchestration. Used to build a ReAct agent that dynamically routes user natural language queries to 8 distinct Python tools.
- **Pandas / RapidFuzz**: Data manipulation and fuzzy string matching. Used for exact filtering and the first step of the location resolution cascade.
- **BeautifulSoup4 / Requests (scraper.py)**: Web scraping. Used for pulling live jobs from Naukri/Jobhai with rotating user-agents.
- **Authlib**: Authentication. Used for seamless Google OAuth login integration.

## 2. ARCHITECTURE MAP

```text
[User Browser]
      | (HTTP/Routes)
[Flask Backend (app.py)]
      |
      +---> [Auth/Session] ----> (Google OAuth / Relational DB)
      |
      +---> [ReAct Agent] -----> (LangChain / Llama 3)
      |         |
      |         +---> [8 Tools: FAISS, Neo4j, Pandas, etc.]
      |
      +---> [Location Cascade]-> (1. RapidFuzz -> 2. Neo4j -> 3. Sector -> 4. RAG)
      |
      +---> [Job Scraper] -----> (Requests/BS4 -> scraped_jobs_cache.json)
```

**Core Files vs Scaffolding:**

1. `app.py`: The monolith core. Initializes Flask, RAG, Neo4j, LangChain agent, and contains the critical `resolve_job_location` logic.
2. `models.py`: The relational schema defining the core business entities (Workers, Companies, Jobs).
3. `build_rag_index.py`: Offline pipeline that embeds 6,002 companies and builds the FAISS index + docs JSON.
4. `load_knowledge_graph.py`: Offline pipeline that populates the Neo4j graph nodes and relationships from CSV.
5. `scraper.py`: Fallback-enabled live job scraper.

## 3. KEY ALGORITHMS / LOGIC

- **4-Step Location Resolver (`resolve_job_location`)**
  - _Plain English_: Figures out exactly where a job is on a map, even if the posting just says "Pune". It checks the exact company name, then relationships, then guesses by industry, and finally uses AI to find the closest match.
  - _Technical_: A cascade algorithm: 1) RapidFuzz token sort against 6,002 companies. 2) Neo4j Cypher `LOCATED_IN` lookup. 3) Keyword frequency analysis mapping sector to highest-probability zone. 4) FAISS cosine similarity semantic fallback.
- **RAG Semantic Search (`_faiss_search`)**
  - _Plain English_: Converts text into numbers to find companies that mean the same thing, even if they don't use the same words (e.g., "car maker" = "Automotive").
  - _Technical_: Encodes query to a 384-D vector via `SentenceTransformer`, normalizes it, and queries a FAISS `IndexFlatIP` (inner product) for cosine similarity with a 0.25 threshold.
- **ReAct Agent Routing**
  - _Plain English_: An AI brain that reads a user question, decides which of 8 database tools has the answer, uses the tool, and summarizes the result.
  - _Technical_: LangChain `create_react_agent` orchestrates an LLM through a Thought -> Action -> Observation loop, feeding it typed tool descriptions (e.g., `tool_neo4j_zone_profile`).
  - _Flag_: Agent logic heavily depends on prompt engineering in tool docstrings. If it hallucinates, it's because tool descriptions overlap.

## 4. DESIGN DECISIONS + TRADEOFFS

- **Knowledge Graph (Neo4j) vs Relational DB**
  - _Chosen_: Neo4j for topological data (Zones, Industries).
  - _Alternative_: Complex SQL JOINs in SQLite.
  - _Tradeoff_: Graph DB makes structural queries (`(Company)-[:LOCATED_IN]->(Zone)`) incredibly fast and readable, but adds infrastructure complexity (needs a separate DB instance).
- **FAISS vs Vector-Enabled SQL (pgvector)**
  - _Chosen_: FAISS flat index (`IndexFlatIP`).
  - _Alternative_: PostgreSQL with pgvector.
  - _Tradeoff_: FAISS is blazing fast, in-memory, and easy to deploy locally without modifying the existing SQLite setup. Loses out on ACID compliance for vector updates (requires full rebuild).
- **Static Seed Data Fallback for Scraper**
  - _Chosen_: Requests/BS4 with a hardcoded static seed data fallback.
  - _Alternative_: Pure live scraping via Selenium.
  - _Tradeoff_: Highly reliable for demos/interviews; won't break if Naukri changes their DOM. Interviewers will poke at brittleness of BS4 scraping.

## 5. INTERVIEW-READY SUMMARY (STAR FORMAT)

- **30-Second Pitch**: IndusTech is a comprehensive industrial ecosystem platform for Pune's MIDC zones. It combines a job portal and an AI-powered company discovery engine using a Neo4j Knowledge Graph and FAISS semantic search to perfectly match jobs and companies to their physical zones.
- **2-Minute Deep Dive**:
  - **Situation**: Pune's MIDC has thousands of companies but no unified digital ecosystem, making it hard for workers to find precise job locations and businesses to find ecosystem partners.
  - **Task**: I needed to build a platform bridging industrial networking and recruitment while solving the ambiguous location data problem (e.g., job postings just saying "Pune").
  - **Action**: I built a Flask monolith backed by SQLite for state, integrated a Neo4j Knowledge Graph for structural queries, built a FAISS vector index for semantic company search, and implemented a custom 4-step algorithmic cascade to accurately geolocate jobs. I tied this together with a LangChain ReAct agent.
  - **Result**: The platform dynamically routes user queries to the correct database (Graph, Vector, or SQL) and accurately plots scraped jobs on an interactive map, creating a seamless industrial ecosystem.

## 6. ANTICIPATED QUESTIONS + ANSWERS

1. **Why FAISS instead of pgvector?** "Speed of implementation and memory control. FAISS runs purely in-memory and handles 6,000 vectors effortlessly without needing a Postgres upgrade."
2. **Explain the 4-step location resolver.** "It's a cascade to combat vague data: 1) RapidFuzz exact company match, 2) Neo4j Knowledge Graph lookup, 3) Keyword-based sector-to-zone probability, 4) FAISS semantic fallback."
3. **How do you handle graph and relational DB sync?** "Currently, they are separated by concern. Relational handles state (users, jobs) and graph handles read-heavy topological data. They are synced offline."
4. **What if the job scraper gets blocked?** "I implemented rotating user-agents and a static seed data fallback to ensure the map always has data for demonstrations."
5. **What was the hardest part?** "Tuning the ReAct agent to pick the right tool among 8 options without hallucinating parameters. I solved it by strictly typing tool docstrings."
6. **Why use a local SentenceTransformer model?** "Cost and latency. `all-MiniLM-L6-v2` is lightweight enough to run on CPU and avoids OpenAI API calls for every search."
7. **What happens if a company is in multiple zones?** "The Knowledge Graph maps a 1:1 `LOCATED_IN` relationship based on HQ. For multi-branch, the schema would need an `OFFICE_IN` edge."
8. **Why Flask and not FastAPI?** "Flask's templating engine was perfect for rendering the frontend views directly, whereas FastAPI is strictly API-first."
9. **How would you scale this to all of India?** "I'd move the FAISS index to a managed vector DB like Pinecone, cluster the Neo4j instances, and refactor the Flask monolith into microservices."
10. **Explain the ReAct Agent.** "It uses LangChain to give Llama 3 a 'Thought -> Action -> Observation' loop. It reads the prompt, decides which of my Python tools to call, and formats the answer."
11. **What if the LLM goes offline?** "I built a fallback: it bypasses the agent and performs a simple RAG search against FAISS, appending the context to a basic generation call."
12. **Why use inner product for FAISS?** "Because I normalize the vectors first (`np.linalg.norm`). Inner product on normalized vectors is mathematically equivalent to cosine similarity but faster."
13. **How do you prevent SQL injection in the company filter tool?** "I don't pass raw SQL to the tool; it accepts a JSON string, parses it, and uses Pandas dataframe filtering (`_midc_df.copy()`)."
14. **Why rapidfuzz instead of standard fuzzywuzzy?** "RapidFuzz is implemented in C++ and is significantly faster for matching against a list of 6,000 companies."
15. **What would you do differently?** "I'd separate the frontend into a React SPA. Having the AI logic and the HTML rendering in one monolith makes `app.py` over 3,000 lines long."

## 7. WEAK SPOTS TO PRE-EMPT

- **Monolith Size**: `app.py` is >3000 lines. _Answer_: "It's a monolith for rapid prototyping. In production, I would break this into Flask Blueprints (Auth, RAG, Jobs)."
- **Scraper Brittle**: BS4 relies on DOM classes. _Answer_: "Web scraping is inherently brittle. The seed data fallback guarantees demo stability; production would use official APIs."
- **Offline DB Sync**: FAISS and Neo4j are built via offline scripts. _Answer_: "Real-time sync wasn't the goal for v1. A message queue (Kafka) would be needed to update the vector/graph DBs on new company registration."

## 8. METRICS / RESULTS CHECK

- **Cite**: 6,002 MIDC Companies indexed.
- **Cite**: 15 MIDC Zones mapped.
- **Cite**: 8 distinct ReAct Agent Tools.
- **Cite**: 384-dimensional embeddings (all-MiniLM-L6-v2).
- **Cite**: ~50m exact match accuracy in Location Resolver (via RapidFuzz).
- **DO NOT CITE**: Real-time graph updates (it's built via offline script).
- **DO NOT CITE**: 100% scraper uptime (it falls back to seed data).
