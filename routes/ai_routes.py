from flask import Blueprint, jsonify, request
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from ai_engine.rag_service import rag_engine

ai_bp = Blueprint('ai', __name__)

@ai_bp.route("/api/v1/recommendations/jobs", methods=["POST"])
def api_recommend_jobs():
    data = request.get_json() or {}
    query = data.get("query", "")
    top_k = data.get("top_k", 5)
    
    results = rag_engine.search_jobs(query, top_k=top_k)
    return jsonify({"status": "success", "count": len(results), "jobs": results})

@ai_bp.route("/api/v1/recommendations/suppliers", methods=["POST"])
def api_recommend_suppliers():
    data = request.get_json() or {}
    query = data.get("query", "")
    top_k = data.get("top_k", 5)
    
    results = rag_engine.search_suppliers(query, top_k=top_k)
    return jsonify({"status": "success", "count": len(results), "products": results})

@ai_bp.route("/api/v1/chat", methods=["POST"])
def api_chat():
    data = request.get_json() or {}
    message = data.get("message", "")
    
    reply, jobs, products = rag_engine.generate_chat_response(message)
    return jsonify({
        "status": "success",
        "reply": reply,
        "matched_jobs": jobs,
        "matched_products": products
    })

from ai_engine.knowledge_graph import kg_engine

@ai_bp.route("/api/v1/graph/search", methods=["GET"])
def api_graph_search():
    query = request.args.get("q", "")
    graph_data = kg_engine.search_graph(query)
    return jsonify(graph_data)

@ai_bp.route("/api/v1/graph/full", methods=["GET"])
def api_graph_full():
    return jsonify(kg_engine.get_full_graph())

