"""
indusconnect/ingestion.py
=========================
Full pipeline orchestrator for daily Adzuna job ingestion.

Pipeline:
  1. Fetch jobs from Adzuna (paginated, retry, dedup)
  2. Normalize raw data
  3. Clean job descriptions
  4. Resolve KG Zone and Industry (Neo4j)
  5. Generate embeddings (SentenceTransformer)
  6. Upsert to database (AdzunaJob)
  7. Mark stale jobs inactive
  8. Rebuild FAISS index
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional
from database import db
from indusconnect.adzuna import AdzunaClient, normalize_job
from indusconnect.cleaning import clean_job_description, build_embedding_text
from indusconnect.kg_resolver import resolve_job_zone
from indusconnect.embedding import embed_texts
from indusconnect.models_ic import AdzunaJob
from indusconnect.retrieval import build_faiss_index

logger = logging.getLogger("[INGESTION]")

def run_ingestion_pipeline(neo4j_driver=None) -> dict:
    """
    Run the end-to-end ingestion pipeline.
    Must be called within a Flask application context.
    
    Returns:
        dict of ingestion statistics
    """
    stats = {
        "start_time": datetime.utcnow(),
        "jobs_received": 0,
        "jobs_normalized": 0,
        "jobs_cleaned": 0,
        "jobs_zone_tagged": 0,
        "jobs_without_zone": 0,
        "new_jobs": 0,
        "updated_jobs": 0,
        "stale_jobs_deactivated": 0,
        "embeddings_generated": 0,
        "vector_index_size": 0,
        "status": "success",
        "error": None
    }
    
    try:
        # 1. Fetch from Adzuna
        client = AdzunaClient()
        raw_jobs = client.fetch_all_terms()
        stats["jobs_received"] = len(raw_jobs)
        
        if not raw_jobs:
            logger.warning("No jobs received from Adzuna.")
            return stats
            
        normalized_jobs = []
        for raw in raw_jobs:
            norm = normalize_job(raw)
            if norm:
                normalized_jobs.append(norm)
                
        stats["jobs_normalized"] = len(normalized_jobs)
        
        # 2-4. Process each job (Clean, KG Tag, Prepare Embedding Text)
        jobs_to_embed = []  # List of dicts
        embedding_texts = [] # List of strings to embed in batch
        
        for job in normalized_jobs:
            # 3. Clean
            job["description"] = clean_job_description(job["description"])
            stats["jobs_cleaned"] += 1
            
            # 4. Resolve KG Zone
            zone, industry = resolve_job_zone(
                neo4j_driver,
                company_name=job["company_name"],
                location_display=job["location_display"],
                location_area=job["location_area"],
                description=job["description"]
            )
            job["midc_zone"] = zone
            job["industry"] = industry
            
            if zone:
                stats["jobs_zone_tagged"] += 1
            else:
                stats["jobs_without_zone"] += 1
                
            # Prepare for embedding
            text_to_embed = build_embedding_text(job)
            if text_to_embed:
                jobs_to_embed.append(job)
                embedding_texts.append(text_to_embed)
                
        # 5. Batch Embeddings
        if embedding_texts:
            logger.info(f"Generating embeddings for {len(embedding_texts)} jobs...")
            embeddings = embed_texts(embedding_texts)
            stats["embeddings_generated"] = len(embeddings)
            
            # Combine back
            for job, vec in zip(jobs_to_embed, embeddings):
                job["embedding_vec"] = vec
                
        # 6. Database Upsert
        now = datetime.utcnow()
        for job_data in jobs_to_embed:
            # Check if exists
            existing = AdzunaJob.query.filter_by(source_job_id=job_data["source_job_id"]).first()
            
            if existing:
                # Update
                existing.title = job_data["title"]
                existing.description = job_data["description"]
                existing.company_name = job_data["company_name"]
                existing.location_display = job_data["location_display"]
                existing.location_area = job_data["location_area"]
                existing.latitude = job_data["latitude"]
                existing.longitude = job_data["longitude"]
                existing.midc_zone = job_data["midc_zone"]
                existing.industry = job_data["industry"]
                existing.category_label = job_data["category_label"]
                existing.category_tag = job_data["category_tag"]
                existing.contract_type = job_data["contract_type"]
                existing.contract_time = job_data["contract_time"]
                existing.salary_min = job_data["salary_min"]
                existing.salary_max = job_data["salary_max"]
                existing.salary_is_predicted = job_data["salary_is_predicted"]
                
                # Update embedding if we have a new one
                if "embedding_vec" in job_data:
                    existing.set_embedding(job_data["embedding_vec"])
                
                existing.set_raw(job_data["raw_source_data"])
                existing.last_seen_at = now
                existing.active = True # reactivate if it was inactive
                
                stats["updated_jobs"] += 1
            else:
                # Create
                new_job = AdzunaJob(
                    source=job_data["source"],
                    source_job_id=job_data["source_job_id"],
                    title=job_data["title"],
                    description=job_data["description"],
                    company_name=job_data["company_name"],
                    location_display=job_data["location_display"],
                    location_area=job_data["location_area"],
                    latitude=job_data["latitude"],
                    longitude=job_data["longitude"],
                    midc_zone=job_data["midc_zone"],
                    industry=job_data["industry"],
                    category_label=job_data["category_label"],
                    category_tag=job_data["category_tag"],
                    contract_type=job_data["contract_type"],
                    contract_time=job_data["contract_time"],
                    salary_min=job_data["salary_min"],
                    salary_max=job_data["salary_max"],
                    salary_is_predicted=job_data["salary_is_predicted"],
                    created_at=datetime.fromisoformat(job_data["created_at"].replace('Z', '+00:00')) if job_data.get("created_at") else None,
                    redirect_url=job_data["redirect_url"],
                    last_seen_at=now,
                    active=True
                )
                if "embedding_vec" in job_data:
                    new_job.set_embedding(job_data["embedding_vec"])
                new_job.set_raw(job_data["raw_source_data"])
                
                db.session.add(new_job)
                stats["new_jobs"] += 1
                
        # 7. Mark stale jobs inactive (not seen in last 48 hours)
        stale_threshold = now - timedelta(hours=48)
        stale_jobs = AdzunaJob.query.filter(AdzunaJob.active == True, AdzunaJob.last_seen_at < stale_threshold).all()
        for sj in stale_jobs:
            sj.active = False
            stats["stale_jobs_deactivated"] += 1
            
        db.session.commit()
        
        # 8. Rebuild Vector Index
        build_faiss_index()
        # Count active jobs in DB for stats
        stats["vector_index_size"] = AdzunaJob.query.filter_by(active=True).count()
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        db.session.rollback()
        stats["status"] = "error"
        stats["error"] = str(e)
        
    stats["duration_seconds"] = (datetime.utcnow() - stats["start_time"]).total_seconds()
    
    # Print summary
    print("=" * 50)
    print("INDUSCONNECT JOB INGESTION")
    print("=" * 50)
    print(f"Source: Adzuna")
    print(f"Jobs received: {stats['jobs_received']}")
    print(f"Jobs normalized: {stats['jobs_normalized']}")
    print(f"Jobs cleaned: {stats['jobs_cleaned']}")
    print(f"Jobs zone-tagged: {stats['jobs_zone_tagged']}")
    print(f"Jobs without zone: {stats['jobs_without_zone']}")
    print(f"New jobs: {stats['new_jobs']}")
    print(f"Updated jobs: {stats['updated_jobs']}")
    print(f"Stale jobs deactivated: {stats['stale_jobs_deactivated']}")
    print(f"Embeddings generated: {stats['embeddings_generated']}")
    print(f"Vector index size: {stats['vector_index_size']}")
    print(f"Duration: {stats['duration_seconds']:.1f}s")
    print("=" * 50)
    
    return stats
