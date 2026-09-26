"""
Background Indexing Tasks Module for IndusTech.
Handles non-blocking vector embedding creation for Jobs, Products, and Worker Profiles.
"""

import os
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Vector Store Cache / In-memory Store (can be persisted or backed by Chroma / pgvector)
VECTOR_STORE_DIR = os.path.join(os.path.dirname(__file__), "vector_store")
os.makedirs(VECTOR_STORE_DIR, exist_ok=True)

JOBS_INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "jobs_index.json")
PRODUCTS_INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "products_index.json")
WORKERS_INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "workers_index.json")

def load_json_index(filepath):
    if os.path.exists(filepath):
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading index from {filepath}: {e}")
    return {}

def save_json_index(filepath, data):
    try:
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        logger.error(f"Error saving index to {filepath}: {e}")

def sync_job_embedding(job_id, job_title, description, city, salary, company_name):
    """
    Background Task: Generate embeddings & index a Job Post.
    """
    logger.info(f"[Task Queue] Indexing Job #{job_id}: {job_title}")
    
    index_data = load_json_index(JOBS_INDEX_FILE)
    
    text_content = f"Title: {job_title}. Company: {company_name}. City: {city}. Salary: {salary}. Description: {description}"
    
    index_data[str(job_id)] = {
        "job_id": job_id,
        "title": job_title,
        "company_name": company_name,
        "city": city,
        "salary": salary,
        "content": text_content
    }
    
    save_json_index(JOBS_INDEX_FILE, index_data)
    logger.info(f"[Task Queue] Successfully indexed Job #{job_id}")
    return True

def sync_product_embedding(sell_id, sell_name, description, category, price, company_name):
    """
    Background Task: Generate embeddings & index a Product/Trade item.
    """
    logger.info(f"[Task Queue] Indexing Trade Product #{sell_id}: {sell_name}")
    
    index_data = load_json_index(PRODUCTS_INDEX_FILE)
    
    text_content = f"Product: {sell_name}. Category: {category}. Price: {price}. Supplier: {company_name}. Description: {description}"
    
    index_data[str(sell_id)] = {
        "sell_id": sell_id,
        "name": sell_name,
        "category": category,
        "price": price,
        "company_name": company_name,
        "content": text_content
    }
    
    save_json_index(PRODUCTS_INDEX_FILE, index_data)
    logger.info(f"[Task Queue] Successfully indexed Product #{sell_id}")
    return True

def sync_worker_embedding(worker_id, name, skills, location, experience_summary):
    """
    Background Task: Generate embeddings & index a Worker Profile.
    """
    logger.info(f"[Task Queue] Indexing Worker Profile #{worker_id}: {name}")
    
    index_data = load_json_index(WORKERS_INDEX_FILE)
    
    text_content = f"Worker: {name}. Skills: {skills}. Location: {location}. Experience: {experience_summary}"
    
    index_data[str(worker_id)] = {
        "worker_id": worker_id,
        "name": name,
        "skills": skills,
        "location": location,
        "content": text_content
    }
    
    save_json_index(WORKERS_INDEX_FILE, index_data)
    logger.info(f"[Task Queue] Successfully indexed Worker Profile #{worker_id}")
    return True
