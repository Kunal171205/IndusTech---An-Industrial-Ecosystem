"""
indusconnect/retrieval.py
==========================
Job retrieval pipeline (KG-first + FAISS semantic ranking).

Architecture:
  User Query
      ↓
  Zone Detection (Keyword / Alias)
      ↓
  If Zone detected:
      → Query Neo4j for jobs in that Zone
      → Filter FAISS search space to only those jobs
  Else:
      → Search full FAISS index
      ↓
  Semantic Retrieval (FAISS cosine similarity)
      ↓
  Top-K Job Results
"""

import logging
import numpy as np
from typing import List, Optional, Tuple, Dict
from sqlalchemy.orm import Session
from database import db
from indusconnect.models_ic import AdzunaJob
from indusconnect.embedding import embed_single
from indusconnect.kg_resolver import detect_zone_from_text, get_jobs_in_zone

try:
    import faiss
    _FAISS_AVAILABLE = True
except ImportError:
    _FAISS_AVAILABLE = False


logger = logging.getLogger("[RETRIEVAL]")

# ── Singleton FAISS index ─────────────────────────────────────────────────────
_faiss_index = None
_job_id_mapping = []  # Index maps to AdzunaJob.id


def build_faiss_index():
    """
    Build the FAISS IndexFlatIP from active AdzunaJob embeddings in the DB.
    Called at startup and after ingestion.
    """
    global _faiss_index, _job_id_mapping
    
    if not _FAISS_AVAILABLE:
        logger.error("FAISS not installed. Cannot build index.")
        return

    logger.info("Building FAISS index from active AdzunaJobs...")
    
    # Needs Flask app context to query DB, caller should provide it
    jobs = AdzunaJob.query.filter_by(active=True).all()
    
    valid_jobs = []
    embeddings_list = []
    
    for job in jobs:
        vec = job.get_embedding()
        if vec is not None and vec.shape == (384,):
            valid_jobs.append(job.id)
            embeddings_list.append(vec)
            
    if not valid_jobs:
        logger.warning("No active jobs with embeddings found to build index.")
        _faiss_index = None
        _job_id_mapping = []
        return
        
    embeddings_np = np.vstack(embeddings_list).astype(np.float32)
    dim = embeddings_np.shape[1]
    
    # We use IndexFlatIP since embeddings are L2 normalized (IP == Cosine Similarity)
    index = faiss.IndexFlatIP(dim)
    index.add(embeddings_np)
    
    _faiss_index = index
    _job_id_mapping = valid_jobs
    
    logger.info(f"Built FAISS index with {index.ntotal} vectors of dimension {dim}.")


def search_jobs(
    query_text: str, 
    neo4j_driver=None, 
    top_k: int = 10, 
    threshold: float = 0.25
) -> Tuple[List[Dict], Optional[str]]:
    """
    Execute the KG-first search pipeline.
    
    Args:
        query_text: The worker's search query
        neo4j_driver: active Neo4j driver
        top_k: max results to return
        threshold: minimum cosine similarity score
        
    Returns:
        Tuple of (list of job dictionaries, detected_zone_name)
    """
    if not query_text or _faiss_index is None or not _job_id_mapping:
        return [], None
        
    # 1. Embed query
    query_vec = embed_single(query_text)
    if query_vec is None:
        logger.error("Failed to embed query text.")
        return [], None
        
    # 2. Zone Detection (KG-FIRST)
    detected_zone = detect_zone_from_text(query_text)
    
    # 3. Candidate Filtering & Semantic Search
    k_to_search = min(top_k * 4, len(_job_id_mapping))  # Fetch more to filter later
    
    distances, indices = _faiss_index.search(query_vec, k_to_search)
    
    results = []
    
    for dist, idx in zip(distances[0], indices[0]):
        if idx < 0 or idx >= len(_job_id_mapping):
            continue
            
        score = float(dist)
        if score < threshold:
            continue
            
        job_id = _job_id_mapping[idx]
        # Querying DB in a loop is okay for small K, but can be optimized with an IN query
        job = AdzunaJob.query.get(job_id)
        if not job or not job.active:
            continue
            
        # If a zone was detected, apply KG filtering (strict)
        # Note: If no zone detected, we return global results
        if detected_zone and job.midc_zone != detected_zone:
            continue
            
        job_dict = job.to_dict()
        job_dict["similarity_score"] = score
        results.append(job_dict)
        
        if len(results) >= top_k:
            break
            
    # Fallback: if zone filtered out everything, we could fallback to global search
    # But strict adherence to architecture says KG filtering must apply if zone is detected.
    
    logger.info(f"Query: '{query_text}' | Zone: {detected_zone} | Returned: {len(results)}")
    return results, detected_zone

