"""
FastAPI Microservice for IndusTech AI & RAG Engine.
Exposes async endpoints for semantic matching, supplier discovery, and assistant chat.
"""

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import sys
import os

sys.path.append(os.path.dirname(__file__))
from rag_service import rag_engine

app = FastAPI(
    title="IndusTech AI & RAG Engine",
    description="Standalone microservice for semantic job/supplier matching & RAG industrial assistant",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 5

class ChatRequest(BaseModel):
    message: str

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "IndusTech AI Engine", "version": "1.0.0"}

@app.post("/api/v1/recommendations/jobs")
def get_job_recommendations(req: QueryRequest):
    """
    RAG Semantic Match Endpoint for Jobs.
    """
    try:
        results = rag_engine.search_jobs(req.query, top_k=req.top_k)
        return {"status": "success", "count": len(results), "jobs": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/recommendations/suppliers")
def get_supplier_recommendations(req: QueryRequest):
    """
    RAG Semantic Match Endpoint for Industrial Goods & Suppliers.
    """
    try:
        results = rag_engine.search_suppliers(req.query, top_k=req.top_k)
        return {"status": "success", "count": len(results), "products": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/chat")
def chat_assistant(req: ChatRequest):
    """
    RAG Industrial Assistant Endpoint.
    """
    try:
        answer, jobs, products = rag_engine.generate_chat_response(req.message)
        return {
            "status": "success",
            "reply": answer,
            "matched_jobs": jobs,
            "matched_products": products
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
