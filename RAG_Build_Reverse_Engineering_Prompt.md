# RAG Build Reverse-Engineering Prompt

## Role

Act as a **Senior RAG Engineer, AI/ML Engineer, Python Backend Engineer, and Technical Interview Coach**.

I will provide you with the source code of a RAG-based project.

The code may have been AI/vibe-coded, and I do not fully understand how the RAG was built.

Your primary objective is **NOT to summarize the project**.

Your objective is to **reverse-engineer how the RAG was actually constructed from the code**, so that I can independently understand, explain, debug, and modify it.

I want to understand the RAG as if I had personally built it.

---

# CORE OBJECTIVE

Reconstruct the complete RAG construction process from the actual code:

```text
DOCUMENT
   ↓
DOCUMENT LOADING
   ↓
TEXT EXTRACTION
   ↓
TEXT CLEANING
   ↓
CHUNKING
   ↓
CHUNK METADATA
   ↓
DOCUMENT EMBEDDINGS
   ↓
VECTOR STORAGE
   ↓
USER QUERY
   ↓
QUERY EMBEDDING
   ↓
VECTOR SEARCH
   ↓
TOP-K RETRIEVED CHUNKS
   ↓
FILTERING / RERANKING
   ↓
CONTEXT CONSTRUCTION
   ↓
PROMPT CONSTRUCTION
   ↓
LLM
   ↓
GENERATED ANSWER
```

But **DO NOT assume this pipeline exists**.

Inspect the actual code and replace each stage with the actual implementation.

If a stage does not exist, explicitly say:

> **Not implemented in the provided code.**

If it cannot be determined:

> **Cannot be determined from the provided code.**

---

# 1. FIRST UNDERSTAND THE PROJECT

Before explaining RAG theory, inspect the complete project.

Identify:

- All important folders
- All Python files
- Entry point
- Configuration
- Data/document folders
- Ingestion scripts
- Retrieval code
- Embedding code
- Vector database/index
- Prompt code
- LLM code
- API/backend
- Utility modules
- Requirements/dependencies
- Environment variables

Create:

| File | Purpose | RAG Stage | Important Functions |
|---|---|---|---|

Do not explain every trivial utility file.

Focus on files that actually contribute to the RAG.

---

# 2. FIND WHERE THE RAG IS CREATED

This is the most important part.

Find the exact code where the RAG system is assembled.

Look for things such as:

```python
embedding_model = ...
vector_store = ...
retriever = ...
llm = ...
chain = ...
```

or custom implementations.

Identify:

- Where the embedding model is initialized
- Where the vector store is initialized
- Where documents are loaded
- Where chunks are created
- Where vectors are generated
- Where vectors are inserted
- Where retrieval is configured
- Where the LLM is initialized
- Where the prompt is created
- Where everything is connected

Show the **actual construction sequence**.

Use actual function names from my project.

---

# 3. EXPLAIN RAG AS TWO SEPARATE PIPELINES

## A. INDEXING / INGESTION PIPELINE

Explain how knowledge gets INTO the RAG.

```text
Documents
    ↓
Loader
    ↓
Text
    ↓
Chunks
    ↓
Embeddings
    ↓
Vector Store
```

## B. QUERY / RETRIEVAL PIPELINE

Explain how knowledge comes OUT of the RAG.

```text
User Question
    ↓
Query Embedding
    ↓
Vector Search
    ↓
Relevant Chunks
    ↓
Context
    ↓
Prompt
    ↓
LLM
    ↓
Answer
```

Explain exactly how these two pipelines are connected.

---

# 4. DOCUMENT INGESTION — HOW WAS THE KNOWLEDGE ADDED?

Find the exact document ingestion code.

Explain:

### Input

What enters the system?

Examples:

- PDF
- TXT
- DOCX
- CSV
- Website
- Database
- Markdown
- JSON

### Loader

Identify the actual library/class/function.

Explain exactly what it returns.

For example:

```text
PDF
 ↓
Loader
 ↓
List[Document]
```

Explain what a `Document` contains:

```text
Document
├── page_content
└── metadata
```

If the project does something different, explain the actual structure.

---

# 5. TEXT EXTRACTION

Explain exactly how raw documents become text.

Trace:

```text
PDF file
   ↓
Parser
   ↓
Raw text
   ↓
Cleaned text
```

Identify:

- Text extraction library
- Cleaning
- Normalization
- Header/footer removal
- Whitespace handling
- OCR if present
- Page handling
- Metadata

If there is no preprocessing, explicitly say so.

---

# 6. CHUNKING — HOW WAS THE DOCUMENT BROKEN DOWN?

Find the exact chunking code.

Identify:

- Chunking library
- Splitter
- Chunk size
- Chunk overlap
- Separators
- Recursive splitting
- Character/token-based splitting
- Metadata preservation

Show an example:

```text
Original Document
       |
       +---- Chunk 1
       |
       +---- Chunk 2
       |
       +---- Chunk 3
```

Explain why chunking is needed, then connect that explanation to the actual code.

---

# 7. UNDERSTAND THE CHUNK OBJECT

Find out what is actually stored for each chunk.

For example:

```python
{
    "text": "...",
    "metadata": {
        "source": "...",
        "page": 4
    }
}
```

Explain:

- Text
- Source
- Page
- Document ID
- Chunk ID
- Other metadata

Then explain where this metadata goes.

---

# 8. EMBEDDING MODEL — HOW TEXT BECOMES A VECTOR

Find the exact embedding model.

Identify:

- Model name
- Library
- Model initialization
- Input format
- Output format
- Embedding dimension
- CPU/GPU
- Normalization
- Batch processing

Explain:

```text
"Eligibility requires applicant age above 18"
                    ↓
             Embedding Model
                    ↓
       [0.12, -0.34, 0.87, ...]
```

Explain that the vector is a numerical representation of semantic meaning.

Then explain the actual code that performs this.

---

# 9. DOCUMENT EMBEDDING PROCESS

Trace exactly what happens during indexing.

```text
Chunk 1 → Embedding Model → Vector 1
Chunk 2 → Embedding Model → Vector 2
Chunk 3 → Embedding Model → Vector 3
```

Then:

```text
Vectors
   ↓
Vector Store
```

Identify the exact function responsible.

Explain whether embeddings are:

- generated once
- regenerated every startup
- generated during upload
- cached
- stored permanently

---

# 10. VECTOR DATABASE / INDEX — HOW THE RAG REMEMBERS DOCUMENTS

Find exactly where the vectors are stored.

Identify:

- Vector database/index
- Initialization
- Index creation
- Insert/add operation
- Persistence
- Loading
- Similarity metric
- Metadata storage

Explain conceptually:

```text
Chunk 1 → Vector 1
Chunk 2 → Vector 2
Chunk 3 → Vector 3
Chunk 4 → Vector 4

              ↓

       VECTOR STORE
```

Then explain what the actual technology does.

---

# 11. SHOW A SMALL CONCRETE EXAMPLE

Use a simplified example based on the actual project.

For example:

```text
"The applicant must be at least 18 years old."
```

Show:

```text
Text
 ↓
Chunk
 ↓
Embedding
 ↓
Vector
 ↓
Stored in Vector DB
```

Then:

```text
"What is the minimum age?"
```

becomes:

```text
Question
 ↓
Query Embedding
 ↓
Similarity Search
 ↓
Matching Chunk
 ↓
LLM
 ↓
Answer
```

---

# 12. QUERY PIPELINE — START FROM THE USER QUESTION

Find exactly where a user question enters the application.

Identify:

- API endpoint
- Function
- Request object
- Parameter
- Query variable

Trace:

```text
User
 ↓
HTTP/API
 ↓
Function
 ↓
Query
```

Use the actual endpoint and function names.

---

# 13. QUERY EMBEDDING

Find the exact code that converts the user query into a vector.

Explain:

```text
User Question
      ↓
Embedding Model
      ↓
Query Vector
```

Determine whether the same embedding model used for documents is used for the query.

Explain why this matters.

---

# 14. VECTOR SEARCH

Find the exact retrieval function.

Explain:

```text
Query Vector
      ↓
Vector Store
      ↓
Similarity Calculation
      ↓
Ranked Results
```

Identify:

- Similarity metric
- Top-K
- Score
- Threshold
- Metadata filter
- Search parameters

Explain exactly what happens to the retrieved results.

---

# 15. EXPLAIN SIMILARITY

If cosine similarity is used, explain:

```text
cosine_similarity(A,B)
=
(A · B) / (||A|| ||B||)
```

Explain in simple terms:

> Vectors pointing in similar directions represent semantically similar text.

Then connect it to the actual vector-store implementation.

If another metric is used, explain that metric instead.

---

# 16. RETRIEVED DOCUMENTS

Show what the retriever actually returns.

For example:

```text
[
   {
      text: "...",
      score: 0.89,
      metadata: {...}
   },
   {
      text: "...",
      score: 0.84,
      metadata: {...}
   }
]
```

Explain:

- Result structure
- Score
- Metadata
- Ordering
- Top-K

Then explain what happens next.

---

# 17. CONTEXT CONSTRUCTION

Find where retrieved chunks are combined into context.

```text
Chunk 1
+
Chunk 2
+
Chunk 3
      ↓
Retrieved Context
```

Identify:

- Function
- Formatting
- Separators
- Metadata
- Maximum context size
- Ordering

Explain exactly how the LLM receives retrieved information.

---

# 18. PROMPT CONSTRUCTION

Find the exact prompt.

Explain the final structure:

```text
SYSTEM INSTRUCTIONS
+
RETRIEVED CONTEXT
+
USER QUESTION
+
OPTIONAL CHAT HISTORY
=
FINAL PROMPT
```

Identify what is actually present.

Explain:

- System prompt
- User prompt
- Retrieved context
- Instructions
- Citation instructions
- Hallucination restrictions
- Formatting requirements
- Conversation history

Show a **sanitized simplified version** of the actual prompt.

Never expose secrets.

---

# 19. LLM GENERATION

Identify:

- LLM
- Provider
- SDK
- Model
- Generation parameters
- Input
- Output

Trace:

```text
Final Prompt
     ↓
LLM
     ↓
Generated Answer
```

Explain exactly how the code calls the model.

---

# 20. FINAL RESPONSE

Trace what happens after the LLM generates the answer.

Determine whether the system:

- Returns raw LLM output
- Parses JSON
- Extracts text
- Adds citations
- Adds sources
- Adds metadata
- Performs validation
- Applies post-processing
- Stores conversation history

Show:

```text
LLM Output
   ↓
Post-processing
   ↓
API Response
   ↓
User
```

---

# 21. COMPLETE RAG CALL GRAPH

Create the actual call graph.

Example:

```text
POST /query
      ↓
query_handler()
      ↓
rag_service.query()
      ↓
embed_query()
      ↓
vector_store.similarity_search()
      ↓
retrieve_chunks()
      ↓
build_context()
      ↓
build_prompt()
      ↓
llm.generate()
      ↓
format_response()
      ↓
return response
```

Use actual function names.

---

# 22. COMPLETE INGESTION CALL GRAPH

Create another graph:

```text
upload_document()
      ↓
load_document()
      ↓
extract_text()
      ↓
split_documents()
      ↓
create_embeddings()
      ↓
store_vectors()
```

Again, use actual function names.

---

# 23. IDENTIFY WHERE EACH RAG COMPONENT LIVES

Create:

| RAG Component | Actual File | Actual Function/Class |
|---|---|---|
| Document Loading | | |
| Text Extraction | | |
| Chunking | | |
| Metadata | | |
| Embedding | | |
| Vector Store | | |
| Query Embedding | | |
| Retrieval | | |
| Filtering | | |
| Reranking | | |
| Context Building | | |
| Prompt | | |
| LLM | | |
| Response | | |

This should become my primary RAG reference table.

---

# 24. EXPLAIN HOW THE COMPONENTS CONNECT

Explain the actual dependency chain:

```text
Document Loader
      ↓
Chunker
      ↓
Embedding Model
      ↓
Vector Store
      ↓
Retriever
      ↓
Prompt Builder
      ↓
LLM
```

For every arrow explain why component A calls/uses component B.

---

# 25. IDENTIFY WHAT IS NOT RAG

Separate actual RAG functionality from supporting code.

```text
RAG Core
├── Chunking
├── Embeddings
├── Vector Store
├── Retrieval
├── Context
└── LLM Generation

Supporting Infrastructure
├── API
├── Authentication
├── Database
├── Logging
├── Configuration
└── File Handling
```

Explain which components are essential to RAG and which merely support the application.

---

# 26. FIND THE "RAG CHAIN"

Determine whether the project uses:

- LangChain
- LlamaIndex
- Haystack
- Custom Python pipeline
- LangGraph
- Other framework

If a framework is used, identify the actual chain.

If it is custom code, explain the equivalent manually constructed pipeline.

---

# 27. DETERMINE HOW MUCH OF THE RAG IS AUTOMATIC

Determine whether the framework handles:

- Chunking
- Embeddings
- Retrieval
- Prompting
- Chain execution
- Output parsing

versus manually implemented code.

Create:

| Functionality | Framework Handles It | Custom Code Handles It |
|---|---|---|
| Loading | | |
| Chunking | | |
| Embeddings | | |
| Retrieval | | |
| Prompt | | |
| Generation | | |

This will help me understand what the developer actually built versus what the library provides.

---

# 28. FIND HIDDEN / IMPORTANT LOGIC

Look specifically for:

- Similarity thresholds
- `top_k`
- `k`
- `score_threshold`
- Metadata filtering
- Context truncation
- Prompt limits
- Token limits
- Retry logic
- Fallback responses
- "I don't know" handling
- Empty retrieval handling
- Query rewriting
- Chat history
- Caching

Explain why each one matters.

---

# 29. IDENTIFY RAG QUALITY CONTROLS

Determine whether the implementation contains:

- Retrieval threshold
- Reranking
- Grounding
- Citation checking
- Context validation
- Hallucination guard
- Abstention
- Answer validation
- Source attribution

For each:

```text
Feature
 ↓
Where implemented
 ↓
How it works
 ↓
What problem it solves
```

---

# 30. EXPLAIN WHY THE RAG WORKS

Explain the core mechanism in simple language:

> The RAG does not train the LLM on the user's documents.

Explain what actually happens:

```text
Documents
   ↓
Converted into searchable vectors
   ↓
Stored externally

Question
   ↓
Converted into a vector
   ↓
Search for similar document chunks
   ↓
Relevant chunks added to prompt
   ↓
LLM generates answer using that context
```

Then map every step to the actual code.

---

# 31. EXPLAIN WHAT WOULD HAPPEN IF I CHANGE SOMETHING

Based on the actual code, explain:

### If I change chunk size

What changes?

### If I change chunk overlap

What changes?

### If I change embedding model

What must be regenerated?

### If I change Top-K

What changes?

### If I remove the vector store

What breaks?

### If I change the prompt

What changes?

### If I change the LLM

What changes?

### If I upload a new document

What happens?

### If I restart the application

What happens to the vectors?

### If the vector database is deleted

What happens?

This section should make me capable of modifying the RAG myself.

---

# 32. DEBUGGING THE RAG

Explain how to debug each stage independently.

## Document Problem

Check:

```text
Document
 ↓
Loader
 ↓
Extracted text
```

## Chunking Problem

Check:

```text
Extracted text
 ↓
Chunks
```

## Embedding Problem

Check:

```text
Chunk
 ↓
Vector
```

## Vector Store Problem

Check:

```text
Vector
 ↓
Stored Index
```

## Retrieval Problem

Check:

```text
Query
 ↓
Query Vector
 ↓
Search Results
```

## Prompt Problem

Check:

```text
Retrieved Chunks
 ↓
Final Prompt
```

## LLM Problem

Check:

```text
Final Prompt
 ↓
LLM
 ↓
Answer
```

Explain what I should print/log/inspect at each stage.

---

# 33. COMMON FAILURE SCENARIOS

Explain exactly what happens if:

- Retrieval returns irrelevant documents
- Retrieval returns zero documents
- Embedding model fails
- Vector database is empty
- Document extraction fails
- LLM fails
- API key is missing
- Context is too large
- Prompt is malformed
- New documents are added

For each:

```text
Failure
 ↓
Where it occurs
 ↓
What code does
 ↓
Result
 ↓
How to debug
```

---

# 34. RAG ARCHITECTURE DIAGRAM

Create a clean final architecture:

```text
                    ┌──────────────────┐
                    │    Documents     │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Document Loader  │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │     Chunking     │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │   Embeddings     │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │  Vector Store    │
                    └────────┬─────────┘
                             │
                             │
User Query ───────────────→ Retrieval
                             ↓
                    ┌──────────────────┐
                    │ Retrieved Chunks │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │ Prompt Builder   │
                    └────────┬─────────┘
                             ↓
                    ┌──────────────────┐
                    │       LLM        │
                    └────────┬─────────┘
                             ↓
                         Answer
```

Replace all components with the actual project technologies.

---

# 35. INTERVIEW QUESTIONS BASED ON HOW THE RAG WAS BUILT

Create questions specifically around the actual implementation.

- RAG Fundamentals — 10
- Document Processing — 10
- Chunking — 10
- Embeddings — 10
- Vector Database — 10
- Retrieval — 10
- Prompt Engineering — 10
- LLM — 10
- Code Tracing — 10
- Debugging — 10

Do not ask generic questions unrelated to the implementation.

---

# 36. INTERVIEW ANSWERS

For every important question provide:

### Short Answer

2–3 sentences.

### Technical Answer

Detailed answer.

### Code Reference

Mention:

```text
file → function/class
```

### If Interviewer Asks "Why?"

Explain the technical reason.

If the actual developer's reason cannot be known:

> "The code does not explicitly state the design reason. Technically, this component is used for..."

---

# 37. TWO-MINUTE "HOW I BUILT THE RAG" ANSWER

Write an interview answer that sounds like I understand the implementation.

It should explain:

1. How documents enter the system.
2. How text is extracted.
3. How documents are chunked.
4. How embeddings are generated.
5. How vectors are stored.
6. How user queries are embedded.
7. How similarity search retrieves relevant chunks.
8. How retrieved chunks become context.
9. How the prompt is constructed.
10. How the LLM generates the final response.

Use actual technologies from my project.

---

# 38. THIRTY-SECOND "HOW I BUILT THE RAG" ANSWER

Create a concise interview answer:

> "I built the RAG by..."

It should be technically accurate and based entirely on the actual code.

---

# 39. RAG CHEAT SHEET

Fill this using the actual implementation:

```text
DOCUMENT SIDE

Document Loader:
Text Extraction:
Preprocessing:
Chunking:
Chunk Size:
Chunk Overlap:
Metadata:

EMBEDDING

Embedding Model:
Embedding Library:
Embedding Dimension:
Normalization:

VECTOR STORE

Vector Store:
Index:
Similarity Metric:
Top-K:
Threshold:
Metadata Filtering:

QUERY SIDE

Query Entry Point:
Query Embedding:
Retrieval Function:
Context Builder:

GENERATION

Prompt Location:
LLM:
LLM Provider:
Temperature:
Max Tokens:

FINAL RESPONSE

Response Function:
Citations:
Sources:
Post-processing:
```

---

# 40. 10 THINGS I MUST REMEMBER

Give me exactly:

> **10 implementation-specific facts that I absolutely must remember for an interview.**

Replace every item with actual project details.

---

# 41. FINAL ANSWER STRUCTURE

The final documentation must follow:

## PART 1 — Project Structure

## PART 2 — Where the RAG Is Built

## PART 3 — Indexing/Ingestion Pipeline

## PART 4 — Chunking

## PART 5 — Embeddings

## PART 6 — Vector Store

## PART 7 — Query/Retrieval Pipeline

## PART 8 — Context Construction

## PART 9 — Prompt Construction

## PART 10 — LLM Generation

## PART 11 — Complete Query Trace

## PART 12 — Complete Ingestion Trace

## PART 13 — Actual RAG Architecture

## PART 14 — Important Files and Functions

## PART 15 — How to Modify the RAG

## PART 16 — How to Debug the RAG

## PART 17 — Limitations / Potential Problems

## PART 18 — Interview Questions

## PART 19 — Interview Answers

## PART 20 — 2-Minute Explanation

## PART 21 — 30-Second Explanation

## PART 22 — Cheat Sheet

## PART 23 — 10 Things I Must Remember

---

# MOST IMPORTANT INSTRUCTION

Do not merely tell me:

> "This project uses embeddings and a vector database."

Instead explain:

> **Which file creates the embedding model → which function receives the chunks → which function generates the vectors → which function stores those vectors → which function embeds the user query → which function performs similarity search → which function constructs the context → which function builds the prompt → which function calls the LLM → which function returns the answer.**

I want to understand the **actual chain of execution**.

The final explanation should make me capable of opening the source code and saying:

> **"I know why this file exists, what this function does, what data enters it, what comes out of it, and how it connects to the next stage of the RAG."**

Do not dump the source code.

**Reverse-engineer it and teach me how it was built.**

# STARTING INSTRUCTION

After I upload/provide the project, do NOT start with generic RAG theory.

First give me only:

1. **Project structure**
2. **Important RAG-related files**
3. **Where the RAG is actually constructed**
4. **The ingestion/indexing pipeline**
5. **The query/retrieval pipeline**
6. **The exact technologies used at each stage**

Then continue with the complete reverse-engineering analysis.
