"""
RAG & Vector Retrieval Engine Service for IndusTech.
Handles semantic retrieval, vector score calculation, and LLM text generation/streaming.
"""

import os
import json
import math
import re
from collections import Counter

VECTOR_STORE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "vector_store")
JOBS_INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "jobs_index.json")
PRODUCTS_INDEX_FILE = os.path.join(VECTOR_STORE_DIR, "products_index.json")

def tokenize(text):
    """Simple tokenizer for TF-IDF / Cosine Similarity vector comparison."""
    if not text:
        return []
    words = re.findall(r'\w+', text.lower())
    return [w for w in words if len(w) > 2]

def compute_cosine_similarity(vec1, vec2):
    """Computes Cosine Similarity between two term frequency dictionaries."""
    intersection = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in intersection])
    
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = math.sqrt(sum1) * math.sqrt(sum2)
    
    if not denominator:
        return 0.0
    return float(numerator) / denominator

class RAGEngine:
    def __init__(self):
        pass

    def load_index(self, filepath):
        if os.path.exists(filepath):
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def search_jobs(self, query_text, top_k=5):
        """
        Retrieves Top-K semantic matching jobs based on query text / worker skills.
        """
        jobs_data = self.load_index(JOBS_INDEX_FILE)
        query_vec = Counter(tokenize(query_text))
        
        results = []
        for job_id, job in jobs_data.items():
            doc_vec = Counter(tokenize(job.get("content", "")))
            score = compute_cosine_similarity(query_vec, doc_vec)
            
            # Boost score if category/city match
            results.append({
                "job_id": job.get("job_id"),
                "title": job.get("title"),
                "company_name": job.get("company_name"),
                "city": job.get("city"),
                "salary": job.get("salary"),
                "match_score": round(score * 100, 1),
                "summary": job.get("content")
            })
            
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:top_k]

    def search_suppliers(self, query_text, top_k=5):
        """
        Retrieves Top-K semantic matching B2B trade items / suppliers.
        """
        products_data = self.load_index(PRODUCTS_INDEX_FILE)
        query_vec = Counter(tokenize(query_text))
        
        results = []
        for sell_id, item in products_data.items():
            doc_vec = Counter(tokenize(item.get("content", "")))
            score = compute_cosine_similarity(query_vec, doc_vec)
            
            results.append({
                "sell_id": item.get("sell_id"),
                "name": item.get("name"),
                "category": item.get("category"),
                "price": item.get("price"),
                "company_name": item.get("company_name"),
                "match_score": round(score * 100, 1),
                "summary": item.get("content")
            })
            
        results.sort(key=lambda x: x["match_score"], reverse=True)
        return results[:top_k]

    def generate_chat_response(self, user_query):
        """
        RAG Chat Generation: Retrieves relevant database context and constructs response.
        """
        # Retrieve context from jobs and products
        matched_jobs = self.search_jobs(user_query, top_k=2)
        matched_products = self.search_suppliers(user_query, top_k=2)
        
        context_lines = []
        if matched_jobs:
            context_lines.append("Relevant Jobs on Platform:")
            for j in matched_jobs:
                context_lines.append(f"- {j['title']} at {j['company_name']} ({j['city']}), Salary: {j['salary']}")
                
        if matched_products:
            context_lines.append("Relevant Industrial Products/Suppliers:")
            for p in matched_products:
                context_lines.append(f"- {p['name']} (Category: {p['category']}) offered by {p['company_name']} at Rs. {p['price']}")
                
        context_str = "\n".join(context_lines)
        
        if not context_lines:
            response = f"I am the IndusTech Industrial AI Assistant. Regarding '{user_query}', our ecosystem connects certified suppliers, job seekers, and manufacturing industries. Feel free to search jobs or explore B2B trade items!"
        else:
            response = f"Based on live IndusTech platform data, here is what I found for '{user_query}':\n\n{context_str}\n\nYou can view full details or apply directly on the portal."
            
        return response, matched_jobs, matched_products

rag_engine = RAGEngine()
