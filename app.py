import email
from enum import unique
from flask import Flask, render_template, request, redirect, session, url_for , jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime , date
from sqlalchemy import Time
import os
import re
from werkzeug.utils import secure_filename
import uuid
from flask import Flask
from database import db
import config
import json
import random
from dotenv import load_dotenv

load_dotenv()

from authlib.integrations.flask_client import OAuth

import secrets

from flask import flash
app = Flask(__name__)
from routes.auth_routes import auth_bp
app.register_blueprint(auth_bp)

app.config.from_object(config)
db.init_app(app)

from models import Worker, TradeRequest , WorkExperience, Certification, Education ,Company, JobPost, sellitem, Application  # import AFTER db.init_app
from indusconnect.models_ic import AdzunaJob

oauth = OAuth(app)

google = oauth.register(
    name="google",
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    access_token_url="https://oauth2.googleapis.com/token",
    authorize_url="https://accounts.google.com/o/oauth2/v2/auth",
    api_base_url="https://www.googleapis.com/oauth2/v2/",
    client_kwargs={
        "scope": "email profile",
        "token_endpoint_auth_method": "client_secret_post"
    }
)



# ================================================================

# RAG + KNOWLEDGE GRAPH + REACT AGENT IMPORTS

# IndusTech journal paper upgrade

# ================================================================

try:
    from neo4j import GraphDatabase
except ImportError:
    print("[IndusTech] WARNING: Neo4j libraries not installed.")
# ================================================================

# RAG + KG STARTUP INITIALIZATION

# All components load once. If any fails, server still starts.

# ================================================================



# --- Neo4j Knowledge Graph ---
_neo4j_driver = None
try:
    _neo4j_driver = GraphDatabase.driver(
        os.getenv("NEO4J_URI", "bolt://localhost:7687"),
        auth=("neo4j", os.getenv("NEO4J_PASSWORD", "password"))
    )
    _neo4j_driver.verify_connectivity()
    print("[IndusTech] Neo4j connected successfully")
except Exception as e:
    _neo4j_driver = None
    print(f"[IndusTech] WARNING: Neo4j unavailable: {e}")

# Build new job FAISS index
from indusconnect.retrieval import build_faiss_index
with app.app_context():
    # Only try to build if tables exist
    try:
        build_faiss_index()
    except Exception as e:
        print(f"Skipping index build (db might not be ready): {e}")

print("[IndusTech] Startup initialization complete.")



# Start ingestion scheduler
from indusconnect.scheduler import start_scheduler
start_scheduler(app, _neo4j_driver)




# ================================================================
# NEW ROUTE: /api/rag-filter
# Semantic filter search for map sidebar filter buttons
# ================================================================
@app.route('/api/rag-filter')
def api_rag_filter():
    rag_query = request.args.get('q', '').strip()
    if not rag_query:
        return jsonify([])

    try:
        user_lat = float(request.args.get('lat'))
        user_lng = float(request.args.get('lng'))
        radius_km = float(request.args.get('radius', 50000)) / 1000
        filter_by_location = True
    except (TypeError, ValueError):
        filter_by_location = False

    from indusconnect.retrieval import search_jobs
    results, _ = search_jobs(rag_query, _neo4j_driver, top_k=30, threshold=0.1)

    output = []
    for job in results:
        lat, lng = job.get('latitude'), job.get('longitude')
        if filter_by_location and lat and lng:
            if haversine_km(user_lat, user_lng, float(lat), float(lng)) > radius_km:
                continue

        output.append({
            "id":           f"rag_{hash(job['source_job_id'])}",
            "title":        job.get('title', 'Unknown'),
            "company":      job.get('company_name', ''),
            "city":         job.get('midc_zone', 'Pune') + " MIDC",
            "type":         job.get('industry', ''),
            "lat":          lat,
            "lng":          lng,
            "rating":       None,
            "website":      job.get('redirect_url', ''),
            "phone":        "",
            "similarity":   round(job.get('similarity_score', 0) * 100, 1),
            "match_type":   "ai_match",
            "source":       "rag",
            "location_confidence": "semantic"
        })

    output.sort(key=lambda x: x['similarity'], reverse=True)
    return jsonify(output[:15])

# ================================================================
# NEW ROUTE: /api/chat
# RAG Chatbot endpoint (Gemini grounded on FAISS retrieval)
# ================================================================
@app.route('/api/chat', methods=['POST'])
def api_chat():
    data     = request.get_json()
    question = data.get('message', '').strip()
    history  = data.get('history', [])

    if not question:
        return jsonify({'answer': 'Please ask a question.', 'sources': [], 'steps': []})

    from indusconnect.retrieval import search_jobs
    results, detected_zone = search_jobs(question, _neo4j_driver, top_k=5)

    faiss_context = ""
    sources = []
    for job in results:
        faiss_context += f"- Title: {job['title']} | Company: {job['company_name']} | Zone: {job['midc_zone']} | Desc: {job['description'][:200]}\n"
        sources.append(job['company_name'])

    history_str = "".join(
        f"User: {t['user']}\nAssistant: {t['assistant']}\n"
        for t in history[-4:]
    )

    zone_str = f"(Detected zone: {detected_zone})\n" if detected_zone else ""

    prompt = (
        f"You are IndusTech AI for Pune MIDC. Answer using only this context.\n\n"
        f"Context:\n{zone_str}{faiss_context}\n\n{history_str}User: {question}\nAssistant:"
    )

    try:
        from google import genai as google_genai
        client = google_genai.Client(api_key=os.getenv('GOOGLE_API_KEY'))
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        answer = response.text.strip()
    except Exception as e:
        answer = f"AI service unavailable: {e}"

    return jsonify({'answer': answer, 'sources': sources, 'steps': [], 'mode': 'rag'})

# ================================================================
# NEW ROUTE: /api/agent-tools
# Returns list of available tools (for frontend display)
# ================================================================
@app.route('/api/agent-tools')
def api_agent_tools():
    # Deprecated UI route, return empty or static tools
    tools = [
        {"name": "SemanticJobSearch", "description": "Find jobs by meaning"},
        {"name": "ZoneProfile",           "description": "Profile of a MIDC zone"},
    ]
    return jsonify({
        "agent_available": False,
        "tools": tools
    })






@app.route("/")
def home():
    jobs = JobPost.query.filter_by(status="Active").order_by(
        JobPost.created_at.desc()
    ).limit(6).all()
    
    total_industries = Company.query.count()
    total_workers = Worker.query.count()
    total_products = sellitem.query.count()
    total_companies = Company.query.count()
    
    companies = Company.query.limit(6).all()
    
    return render_template("home.html", 
                           jobs=jobs,
                           total_industries=total_industries,
                           total_workers=total_workers,
                           total_products=total_products,
                           total_companies=total_companies,
                           companies=companies)

@app.route("/industry-map")
def industrymap():
    search_query = request.args.get("search", "")
    return render_template("industrymap.html", search_query=search_query)

@app.route('/product_view')
def productview():
    return render_template('product_view.html')

@app.route("/support")
def support():
    return render_template("support.html")

import requests
from math import radians, sin, cos, sqrt, atan2

def haversine_km(lat1, lng1, lat2, lng2):
    """Calculate distance in km between two lat/lng points."""
    R = 6371
    dlat = radians(lat2 - lat1)
    dlng = radians(lng2 - lng1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlng/2)**2
    return R * 2 * atan2(sqrt(a), sqrt(1-a))

# City coordinate lookup for Haversine fallback when no lat/lng stored
CITY_COORDS = {
    "pune": (18.5204, 73.8567), "mumbai": (19.0760, 72.8777),
    "nashik": (20.0110, 73.7909), "aurangabad": (19.8762, 75.3433),
    "nagpur": (21.1458, 79.0882), "chakan": (18.7500, 73.8500),
    "satara": (17.6805, 73.9966), "delhi": (28.7041, 77.1025),
    "bangalore": (12.9716, 77.5946), "hyderabad": (17.3850, 78.4867),
    "chennai": (13.0827, 80.2707), "kolkata": (22.5726, 88.3639),
    "ahmedabad": (23.0225, 72.5714), "udgir": (18.3939, 77.1186),
    "latur": (18.3956, 76.5603), "solapur": (17.6868, 75.9064),
    "amravati": (20.9374, 77.7796), "nanded": (19.1383, 77.3210),
}

def get_city_coords(city_str):
    """Return (lat, lng) tuple for a city string, or None if unknown."""
    if not city_str:
        return None
    lower = city_str.lower().strip()
    if lower in CITY_COORDS:
        return CITY_COORDS[lower]
    for key, coords in CITY_COORDS.items():
        if key in lower:
            return coords
    return None

@app.route("/api/map/jobs")
def api_map_jobs():
    # Parse location params
    try:
        user_lat = float(request.args.get("lat"))
        user_lng = float(request.args.get("lng"))
        radius_km = float(request.args.get("radius", 10000)) / 1000
        filter_by_location = True
    except (TypeError, ValueError):
        filter_by_location = False

    keyword = request.args.get("q", "").strip().lower()

    jobs = JobPost.query.filter_by(status="Active").all()
    job_list = []
    
    # Pre-process keyword for text matching
    search_words = keyword.split() if keyword else []

    for job in jobs:
        # Standard text filtering on local DB
        if search_words:
            job_text = f"{job.job_title} {job.company.company_name} {job.city} {job.description}".lower()
            if not all(word in job_text for word in search_words):
                continue

        coords = get_city_coords(job.city)
        if coords:
            lat = round(coords[0] + random.uniform(-0.020, 0.020), 6)
            lng = round(coords[1] + random.uniform(-0.020, 0.020), 6)
            location_confidence = "exact"
        else:
            # Use smart MIDC zone assignment instead of piling all on user location
            lat, lng, location_confidence = resolve_job_location(
                job.job_title or "",
                job.description or "",
                job.city or "",
                company_name=getattr(job, "company_name", "") or ""
            )
        
        if filter_by_location:
            dist = haversine_km(user_lat, user_lng, lat, lng)
            if dist > radius_km:
                continue

        job_list.append({
            "id": job.job_id,
            "title": job.job_title,
            "company": job.company.company_name,
            "city": job.city,
            "location": job.specific_location,
            "salary": job.salary,
            "type": job.job_type,
            "shift": job.shift,
            "description": job.description,
            "source": "local",
            "lat": lat,
            "lng": lng,
            "location_confidence": location_confidence,
        })

    return jsonify(job_list)


# ── All Pune industrial zones with coordinates ───────────────────────────────
# Includes MIDC zones + major IT/industrial hubs in Pune district
PUNE_ALL_ZONES = {
    # Core MIDC zones
    "chakan":       (18.7580, 73.8600),
    "bhosari":      (18.6400, 73.8500),
    "ranjangaon":   (18.7220, 74.1580),
    "hinjewadi":    (18.5910, 73.7380),
    "pirangut":     (18.5100, 73.6900),
    "talawade":     (18.6560, 73.7980),
    "shirwal":      (18.1560, 74.0700),
    "pimpri":       (18.6280, 73.8000),
    "hadapsar":     (18.5020, 73.9360),
    "sanaswadi":    (18.6800, 74.0600),
    # Extended Pune industrial / IT areas
    "magarpatta":   (18.5089, 73.9260),
    "kharadi":      (18.5512, 73.9442),
    "viman nagar":  (18.5679, 73.9143),
    "baner":        (18.5590, 73.7868),
    "wakad":        (18.5985, 73.7610),
    "aundh":        (18.5581, 73.8072),
    "kothrud":      (18.5074, 73.8079),
    "yerawada":     (18.5594, 73.8977),
    "wagholi":      (18.5800, 73.9800),
    "kondhwa":      (18.4627, 73.8797),
    "undri":        (18.4546, 73.9028),
    "talegaon":     (18.7300, 73.6700),
    "khed":         (18.8500, 73.9100),
    "chinchwad":    (18.6440, 73.8015),
}

# MIDC-specific zone subset (for final marker placement)
PUNE_MIDC_ZONES_COORDS = {k: v for k, v in PUNE_ALL_ZONES.items() if k in {
    "chakan","bhosari","ranjangaon","hinjewadi","pirangut",
    "talawade","shirwal","pimpri","hadapsar","sanaswadi",
}}

# ── Company → zone lookup (direct match, highest priority) ───────────────────
# Major companies known to operate in specific Pune zones
COMPANY_TO_ZONE = {
    # Hinjewadi IT companies
    "mastercard":    "hinjewadi", "infosys":       "hinjewadi",
    "wipro":         "hinjewadi", "tech mahindra": "hinjewadi",
    "cognizant":     "hinjewadi", "persistent":    "hinjewadi",
    "tata consultancy": "hinjewadi", "tcs":         "hinjewadi",
    "accenture":     "hinjewadi", "capgemini":     "hinjewadi",
    "oracle":        "hinjewadi", "ibm":           "hinjewadi",
    "zensar":        "hinjewadi", "tieto":         "hinjewadi",
    "kpit":          "hinjewadi",
    # Magarpatta / Kharadi IT
    "barclays":      "kharadi",   "mercedes":      "kharadi",
    "credit suisse": "kharadi",   "deutsche":      "kharadi",
    "hsbc":          "kharadi",
    # Chakan Manufacturing
    "bajaj auto":    "chakan",    "volkswagen":    "ranjangaon",
    "general motors":"talegaon",  "fiat":          "ranjangaon",
    "mercedes benz": "chakan",    "mahindra":      "chakan",
    "tata motors":   "pimpri",    "force motors":  "bhosari",
    "bharat forge":  "bhosari",   "kalyani":       "bhosari",
    "cummins":       "pimpri",    "thermax":       "pimpri",
    "atlas copco":   "hadapsar",  "sandvik":       "sanaswadi",
    "alfa laval":    "pirangut",  "skf":           "ranjangaon",
    "bosch":         "chakan",    "siemens":       "pimpri",
    "abb":           "pimpri",    "honeywell":     "hinjewadi",
    "emerson":       "pimpri",    "parker":        "pimpri",
    "bridgestone":   "ranjangaon","michelin":      "ranjangaon",
    "endurance":     "chakan",    "faurecia":      "chakan",
    "tata consulting": "ranjangaon",
    # Chemical
    "deepak nitrite":"pirangut",  "aarti":         "pirangut",
    "basf":          "shirwal",   "sudarshan":     "shirwal",
    # Logistics
    "dhl":           "hadapsar",  "maersk":        "hadapsar",
    "blue dart":     "hadapsar",  "fedex":         "hadapsar",
    "schenker":      "hadapsar",
}

# ── Keyword → zone (used when company not matched) ───────────────────────────
KEYWORD_TO_ZONE = {
    # IT / Tech (broad) → Hinjewadi
    "software engineer":     "hinjewadi", "senior software":      "hinjewadi",
    "software developer":    "hinjewadi", "python":               "hinjewadi",
    "java":                  "hinjewadi", "react":                "hinjewadi",
    "angular":               "hinjewadi", "node.js":              "hinjewadi",
    "data scientist":        "hinjewadi", "machine learning":     "hinjewadi",
    "artificial intelligence":"hinjewadi","cloud engineer":       "hinjewadi",
    "devops":                "hinjewadi", "site reliability":     "hinjewadi",
    "full stack":            "hinjewadi", "frontend":             "hinjewadi",
    "backend engineer":      "hinjewadi", "mobile developer":     "hinjewadi",
    "ios developer":         "hinjewadi", "android developer":    "hinjewadi",
    "test engineer":         "hinjewadi", "qa engineer":          "hinjewadi",
    "automation testing":    "hinjewadi", "selenium":             "hinjewadi",
    "cybersecurity":         "talawade",  "network engineer":     "talawade",
    "sap consultant":        "talawade",  "erp":                  "talawade",
    "database":              "talawade",  "dba":                  "talawade",
    # Finance / Banking / BFSI → Kharadi / Hinjewadi
    "financial analyst":     "kharadi",   "finance":              "kharadi",
    "investment":            "kharadi",   "banking":              "kharadi",
    "risk analyst":          "kharadi",   "compliance":           "kharadi",
    "credit analyst":        "kharadi",   "treasury":             "kharadi",
    "audit":                 "kharadi",   "chartered accountant": "kharadi",
    # Construction / Projects → Ranjangaon / Pimpri
    "construction manager":  "ranjangaon","site supervisor":      "ranjangaon",
    "construction":          "ranjangaon","site engineer":        "ranjangaon",
    "civil engineer":        "ranjangaon","structural engineer":  "ranjangaon",
    "project engineer":      "pimpri",    "project manager":      "pimpri",
    "commissioning":         "ranjangaon","erection":             "ranjangaon",
    "industrial supervision":"ranjangaon","site management":      "ranjangaon",
    "turnaround":            "ranjangaon","shutdown":             "ranjangaon",
    # Manufacturing → Chakan / Bhosari
    "production supervisor": "chakan",    "production manager":   "chakan",
    "manufacturing":         "chakan",    "plant supervisor":     "chakan",
    "cnc":                   "bhosari",   "vmc":                  "bhosari",
    "machinist":             "bhosari",   "tool & die":           "bhosari",
    "stamping":              "chakan",    "press shop":           "chakan",
    "assembly operator":     "chakan",    "fabrication":          "bhosari",
    "casting":               "chakan",    "forging":              "bhosari",
    "sheet metal":           "bhosari",   "die casting":          "bhosari",
    "plant manager":         "chakan",    "plant head":           "chakan",
    "general manager":       "chakan",    "operations manager":   "chakan",
    "production incharge":   "chakan",    "shift supervisor":     "chakan",
    # Welding → Sanaswadi
    "welding supervisor":    "sanaswadi", "welder":               "sanaswadi",
    "weld inspector":        "sanaswadi", "welding engineer":     "sanaswadi",
    # Mechanical / Electrical Engineering → Pimpri
    "mechanical engineer":   "pimpri",    "electrical engineer":  "pimpri",
    "design engineer":       "pimpri",    "autocad":              "pimpri",
    "solidworks":            "pimpri",    "catia":                "ranjangaon",
    "plc programmer":        "pimpri",    "scada":                "pimpri",
    "automation engineer":   "pimpri",    "instrumentation":      "ranjangaon",
    "hvac":                  "pimpri",    "maintenance engineer":  "ranjangaon",
    "preventive maintenance":"ranjangaon","sales engineer":       "pimpri",
    "industrial automation": "pimpri",
    # Safety / EHS → Shirwal
    "safety officer":        "shirwal",   "hse manager":          "shirwal",
    "ehs officer":           "shirwal",   "fire safety":          "shirwal",
    "environment health":    "shirwal",   "health safety":        "shirwal",
    # Chemical → Pirangut / Shirwal
    "chemical engineer":     "pirangut",  "process engineer":     "pirangut",
    "chemist":               "pirangut",  "pharma":               "shirwal",
    "laboratory analyst":    "pirangut",  "gmp":                  "shirwal",
    "reactor":               "pirangut",  "distillation":         "pirangut",
    # Logistics / Warehouse → Hadapsar
    "logistics manager":     "hadapsar",  "warehouse manager":    "hadapsar",
    "supply chain":          "hadapsar",  "dispatch":             "hadapsar",
    "inventory":             "hadapsar",  "store keeper":         "hadapsar",
    "forklift":              "hadapsar",  "freight":              "hadapsar",
    # Quality → Sanaswadi
    "quality engineer":      "sanaswadi", "quality control":      "sanaswadi",
    "quality assurance":     "sanaswadi", "qc inspector":         "sanaswadi",
    "ppap":                  "ranjangaon","apqp":                 "ranjangaon",
    "iatf":                  "ranjangaon","iso 9001":             "sanaswadi",
    # Sales → Hadapsar / Pimpri
    "sales manager":         "hadapsar",  "business development":  "hadapsar",
    "industrial sales":      "hadapsar",  "b2b sales":            "hadapsar",
    "account manager":       "hadapsar",  "key account":          "hadapsar",
    # HR / Admin → Pimpri
    "hr manager":            "pimpri",    "human resource":       "pimpri",
    "talent acquisition":    "pimpri",    "payroll":              "pimpri",
    "recruitment":           "pimpri",    "purchase manager":     "pimpri",
    "procurement":           "pimpri",    "administration":       "pimpri",
    # Generic tech roles → spread across IT zones
    "program manager":       "hinjewadi", "product manager":      "hinjewadi",
    "scrum master":          "hinjewadi", "agile":                "hinjewadi",
    "architect":             "hinjewadi", "solution architect":   "hinjewadi",
    "technical lead":        "hinjewadi", "tech lead":            "hinjewadi",
    "senior engineer":       "hinjewadi", "principal engineer":   "hinjewadi",
    "vice president":        "kharadi",   "associate director":   "kharadi",
    "director":              "kharadi",   "head of":              "hinjewadi",
}

# ── Industrial corridor spread zones ─────────────────────────────────────────
# IMPORTANT: All corridors must be > 8km from Pune city centre (18.52, 73.85)
# so spread never overlaps with city centre and causes clustering there.
# Verified: min distance from city centre for each corridor ≥ 9km ✓
PUNE_SPREAD_CORRIDORS = [
    # (name,            center_lat, center_lng, spread_deg≈km)
    ("hinjewadi",       18.5910,    73.7380,    0.04),  # 15km west,   ±4km
    ("chakan",          18.7580,    73.8600,    0.04),  # 26km north,  ±4km
    ("bhosari",         18.6400,    73.8500,    0.04),  # 13km north,  ±4km
    ("ranjangaon",      18.7220,    74.1580,    0.04),  # 39km NE,     ±4km
    ("sanaswadi",       18.6800,    74.0600,    0.04),  # 28km NE,     ±4km
    ("hadapsar_east",   18.4900,    74.0000,    0.03),  # 15km east,   ±3km
    ("talegaon",        18.7300,    73.6700,    0.04),  # 31km NW,     ±4km
    ("khed",            18.8500,    73.9100,    0.04),  # 37km north,  ±4km
    ("pirangut",        18.5100,    73.6900,    0.03),  # 18km west,   ±3km
    ("shirwal",         18.1560,    74.0700,    0.04),  # 46km south,  ±4km
    ("talawade",        18.6560,    73.7980,    0.04),  # 16km north,  ±4km
    ("wagholi_east",    18.5800,    74.0100,    0.03),  # 17km east,   ±3km
    ("wakad_west",      18.6100,    73.7200,    0.03),  # 18km west,   ±3km
    ("alandi",          18.7400,    73.8970,    0.03),  # 25km north,  ±3km
    ("urse",            18.7000,    73.6700,    0.03),  # 28km NW,     ±3km
    ("jejuri",          18.2600,    74.1600,    0.03),  # 43km south,  ±3km
]
_corridor_rr = 0

def _spread_coords_in_corridor(corridor):
    """Return random coords within the corridor's spread radius."""
    _, lat, lng, spread = corridor
    return (
        round(lat + random.uniform(-spread, spread), 6),
        round(lng + random.uniform(-spread, spread), 6),
    )

def smart_midc_coords(title, description, area_str):
    """
    Assign a Pune zone coordinate based on:
      1. Exact zone/area name in text  (chakan, hinjewadi, magarpatta...)
      2. Company name lookup           (mastercard → hinjewadi)
      3. Keyword match in title+desc   (longest match first)
      4. Round-robin across 16 spread corridors with WIDE jitter
         — prevents Leaflet from clustering unmatched jobs together
    Returns (lat, lng).
    """
    global _corridor_rr
    combined = f"{title} {description} {area_str}".lower()

    # 1. Direct area/zone name in text
    for zone, coords in PUNE_ALL_ZONES.items():
        if zone in combined:
            # Use corridor spread for this zone if available
            corridor = next((c for c in PUNE_SPREAD_CORRIDORS if c[0] == zone), None)
            if corridor:
                return _spread_coords_in_corridor(corridor)
            return (
                round(coords[0] + random.uniform(-0.030, 0.030), 6),
                round(coords[1] + random.uniform(-0.030, 0.030), 6),
            )

    # 2. Company name lookup
    for company_kw, zone in COMPANY_TO_ZONE.items():
        if company_kw in combined:
            corridor = next((c for c in PUNE_SPREAD_CORRIDORS if c[0] == zone), None)
            if corridor:
                return _spread_coords_in_corridor(corridor)
            coords = PUNE_ALL_ZONES.get(zone, (18.5910, 73.7380))
            return (
                round(coords[0] + random.uniform(-0.030, 0.030), 6),
                round(coords[1] + random.uniform(-0.030, 0.030), 6),
            )

    # 3. Keyword match — longer = more specific → checked first
    for keyword in sorted(KEYWORD_TO_ZONE.keys(), key=len, reverse=True):
        if keyword in combined:
            zone = KEYWORD_TO_ZONE[keyword]
            corridor = next((c for c in PUNE_SPREAD_CORRIDORS if c[0] == zone), None)
            if corridor:
                return _spread_coords_in_corridor(corridor)
            coords = PUNE_ALL_ZONES.get(zone, (18.5910, 73.7380))
            return (
                round(coords[0] + random.uniform(-0.030, 0.030), 6),
                round(coords[1] + random.uniform(-0.030, 0.030), 6),
            )

    # 4. Round-robin across 16 spread corridors — WIDE spread prevents clustering
    corridor = PUNE_SPREAD_CORRIDORS[_corridor_rr % len(PUNE_SPREAD_CORRIDORS)]
    _corridor_rr += 1
    return _spread_coords_in_corridor(corridor)


# ── Adzuna in-memory cache ────────────────────────────────────────────────────
# Stores pre-processed jobs so map requests are instant after first load.
# Cache refreshes automatically every 30 minutes in the background.
@app.route("/api/map/trades")
def api_map_trades():
    try:
        user_lat = float(request.args.get("lat"))
        user_lng = float(request.args.get("lng"))
        radius_km = float(request.args.get("radius", 10000)) / 1000
        filter_by_location = True
    except (TypeError, ValueError):
        filter_by_location = False

    trades = sellitem.query.all()
    trade_list = []
    for trade in trades:
        coords = get_city_coords(trade.company.company_city)
        if coords:
            lat, lng = coords
            location_confidence = "city_center"
        elif filter_by_location:
            lat, lng = user_lat, user_lng
            location_confidence = "fallback_user_location"
        else:
            continue
            
        lat += random.uniform(-0.015, 0.015)
        lng += random.uniform(-0.015, 0.015)
        
        if filter_by_location:
            dist = haversine_km(user_lat, user_lng, lat, lng)
            if dist > radius_km:
                continue

        trade_list.append({
            "id": trade.sell_id,
            "name": trade.sell_name,
            "company": trade.company.company_name,
            "city": trade.company.company_city,
            "location": trade.company.address,
            "price": trade.sell_price,
            "category": trade.sell_category,
            "description": trade.sell_description,
            "quantity": trade.sell_quantity,
            "lat": lat,
            "lng": lng,
            "location_confidence": location_confidence,
        })
    return jsonify(trade_list)

@app.route("/api/map/companies")
def api_map_companies():
    try:
        user_lat = float(request.args.get("lat"))
        user_lng = float(request.args.get("lng"))
        radius_km = float(request.args.get("radius", 10000)) / 1000
        filter_by_location = True
    except (TypeError, ValueError):
        filter_by_location = False

    companies = Company.query.all()
    company_list = []
    for comp in companies:
        coords = get_city_coords(comp.company_city)
        if filter_by_location and coords:
            dist = haversine_km(user_lat, user_lng, coords[0], coords[1])
            if dist > radius_km:
                continue
        company_list.append({
            "id": comp.id,
            "name": comp.company_name,
            "category": comp.company_category,
            "city": comp.company_city,
            "location": comp.address,
            "lat": coords[0] if coords else None,
            "lng": coords[1] if coords else None,
        })
    return jsonify(company_list)


@app.route("/jobportal")
def jobportal():
    page = request.args.get("page", 1, type=int)
    per_page = 12

    category = request.args.get("category")
    city = request.args.get("city")
    shift = request.args.get("shift")
    salary = request.args.get("salary", type=int)
    openings = request.args.get("openings", type=int)

    query = JobPost.query.filter_by(status="Active")

    if category:
        query = query.filter(JobPost.job_title.ilike(f"%{category}%"))

    if city:
        query = query.filter(JobPost.city.ilike(f"%{city}%"))

    if shift:
        query = query.filter(JobPost.shift == shift)

    if salary:
        query = query.filter(
            JobPost.salary.cast(db.Integer) >= salary
        )

    if openings:
        query = query.filter(JobPost.job_opening_no >= openings)

    pagination = query.order_by(
        JobPost.created_at.desc()
    ).paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )

    return render_template(
        "jobportal.html",
        jobs=pagination.items,
        pagination=pagination
    )


@app.route("/trade/<int:sell_id>")
def tradevisit(sell_id):
    sell = sellitem.query.get_or_404(sell_id)

    worker = None
    if session.get("user_type") == "worker":
        worker = Worker.query.get(session.get("worker_id"))

    images = []
    if sell.sell_image:
        images = json.loads(sell.sell_image)  

    worker_age = None
    if worker and worker.dob:
        today = date.today()
        worker_age = today.year - worker.dob.year - (
            (today.month, today.day) < (worker.dob.month, worker.dob.day)
        )

    return render_template(
        "product_view.html",
        sell=sell,
        images=images
    )

@app.route("/job/<int:job_id>")
def jobvisit(job_id):
    job = JobPost.query.get_or_404(job_id)

    worker = None
    if session.get("user_type") == "worker":
        worker = Worker.query.get(session.get("worker_id"))
     
    worker_age = None
    if worker and worker.dob:
        today = date.today()
        worker_age = today.year - worker.dob.year - (
            (today.month, today.day) < (worker.dob.month, worker.dob.day)
        )

    return render_template(
        "jobvisit.html",
        job=job,
        worker=worker,
        worker_age=worker_age
    )


from sqlalchemy.exc import SQLAlchemyError
from flask import abort

@app.route("/application/<int:application_id>/status", methods=["POST"])
def update_application_status(application_id):

    # Only company allowed
    if session.get("user_type") != "company":
        abort(403)

    new_status = request.form.get("status")  # Accepted / Rejected

    application = Application.query.get_or_404(application_id)
    job = application.job

    # Ownership check
    if job.company_id != session.get("company_id"):
        abort(403)

    # Already processed — STOP
    if application.applicant_status != "pending":
        flash("This application has already been processed.", "warning")
        return redirect(request.referrer)

    try:
        if new_status == "Accepted":

            # No openings left
            if job.job_opening_no <= 0:
                flash("No openings left for this job.", "danger")
                return redirect(request.referrer)

            # Accept
            application.applicant_status = "Accepted"
            job.job_opening_no -= 1

            # Auto close job
            if job.job_opening_no == 0:
                job.status = "Closed"

        elif new_status == "Rejected":
            application.applicant_status = "Rejected"

        else:
            flash("Invalid action", "danger")
            return redirect(request.referrer)

        db.session.commit()
        flash("Application updated successfully.", "success")

    except SQLAlchemyError:
        db.session.rollback()
        flash("Database error. Try again.", "danger")

    return redirect(request.referrer)

@app.route("/company/application/<int:application_id>/delete", methods=["POST"])
def delete_company_application(application_id):
    if session.get("user_type") != "company":
        return redirect(url_for('auth_bp.login'))

    application = Application.query.get_or_404(application_id)

    # security check
    if application.job.company_id != session.get("company_id"):
        abort(403)

    db.session.delete(application)
    db.session.commit()

    flash("Application removed successfully", "success")
    return redirect(request.referrer)

@app.route("/company/trade/<int:sell_id>/applications")
def view_trade_applications(sell_id):

    if session.get("user_type") != "company":
        return redirect(url_for('auth_bp.login'))

    company_id = session.get("company_id")

    item = sellitem.query.filter_by(
        sell_id=sell_id,
        company_id=company_id
    ).first_or_404()

    applications = TradeRequest.query.filter_by(
        sell_id=sell_id
    ).order_by(
        TradeRequest.created_at.desc()
    ).all()

    return render_template(
        "trade_application.html",
        item=item,
        applications=applications
    )


@app.route("/company/job/<int:job_id>/applications")
def view_job_applications(job_id):
    if session.get("user_type") != "company":
        return redirect(url_for('auth_bp.login'))

    company_id = session.get("company_id")

    job = JobPost.query.filter_by(
        job_id=job_id,
        company_id=company_id
    ).first_or_404()

    applications = Application.query.filter_by(job_id=job_id)\
                                    .order_by(Application.application_date.desc())\
                                    .all()

    return render_template(
        "job_applications.html",
        job=job,
        applications=applications
    )

@app.route("/worker/<int:worker_id>")
def workerprofile_public(worker_id):
    # Only company can view worker public profile
    if session.get("user_type") != "company":
        return redirect(url_for('auth_bp.login'))

    worker = Worker.query.get_or_404(worker_id)

    return render_template(
        "workerpublic.html",
        worker=worker
    )


@app.route("/company/<int:company_id>")
def companyprofile_public(company_id):
    company = Company.query.get_or_404(company_id)
    jobs = JobPost.query.filter_by(
        company_id=company.id,
        status="Active"
    ).all()

    return render_template(
        "company.html",
        company=company,
        jobs=jobs
    )

@app.route('/trade')
def trade():
    page = request.args.get("page", 1, type=int)
    per_page = 9

    date = request.args.get("date")
    qty = request.args.get("qty")
    price = request.args.get("price")

    query = sellitem.query

    # Quantity filter
    if qty == "050":
        query = query.filter(sellitem.sell_quantity < 50)
    elif qty == "50100":
        query = query.filter(sellitem.sell_quantity >= 50)
    elif qty == "100":
        query = query.filter(sellitem.sell_quantity >= 100)

    # Date sort
    if date == "NF":
        query = query.order_by(sellitem.created_at.desc())
    elif date == "OF":
        query = query.order_by(sellitem.created_at.asc())

    # Price sort
    if price == "l2h":
        query = query.order_by(sellitem.sell_price.asc())
    elif price == "h2l":
        query = query.order_by(sellitem.sell_price.desc())

    pagination = query.paginate(
        page=page,
        per_page=per_page,
        error_out=False
    )
    for item in pagination.items:
        if item.sell_image:
            try:
                item.images = json.loads(item.sell_image)
            except Exception:
                item.images = [item.sell_image]
        else:
            item.images = []
    return render_template(
        "trade.html",
        sell_items=pagination.items,
        pagination=pagination
    )

@app.route('/company/job/delete/<int:job_id>', methods=['POST'])
def delete_job(job_id):
    job = JobPost.query.get_or_404(job_id)
    db.session.delete(job)
    db.session.commit()
    return redirect(url_for('companyprofile'))


@app.route('/company/trade/delete/<int:sell_id>', methods=['POST'])
def delete_trade(sell_id):
    item = sellitem.query.get_or_404(sell_id)
    db.session.delete(item)
    db.session.commit()
    return redirect(url_for('companyprofile'))





@app.route("/signup/worker", methods=["POST"])
def signup_worker():
    worker = Worker(
        name=request.form["full_name"],
        email=request.form["mail"],
        password=request.form["password"]
    )
    db.session.add(worker)
    db.session.commit()

    session["worker_id"] = worker.id
    session["user_type"] = "worker"
    return redirect(url_for("workerprofile"))

@app.route("/worker-profile")
def workerprofile():
    if session.get("user_type") != "worker":
        return redirect(url_for('auth_bp.login'))

    worker_id = session.get('worker_id')
    worker = Worker.query.get(session["worker_id"])
    initial = worker.name[0].upper() if worker.name else "U"

    applications = Application.query \
        .filter_by(worker_id=worker_id) \
        .order_by(Application.application_date.desc()) \
        .all()

    return render_template(
        "workerprofile.html",
        worker=worker,
        initial=initial,
        applications=applications
    )

@app.route('/worker/application/delete/<int:app_id>', methods=['POST'])
def delete_worker_application(app_id):
    if session.get("user_type") != "worker":
        abort(403)

    app = Application.query.get_or_404(app_id)

    if app.worker_id != session.get('worker_id'):
        abort(403)

    if app.applicant_status != "pending":
        flash("You cannot delete a processed application", "warning")
        return redirect(url_for("workerprofile"))

    db.session.delete(app)
    db.session.commit()
    flash("Application deleted", "success")
    return redirect(url_for('workerprofile'))


@app.route('/application/edit', methods=['POST'])
def edit_application():
    app = Application.query.get_or_404(request.form['application_id'])

    if app.worker_id != session.get('worker_id'):
        abort(403)

    app.applicant_skill = request.form['applicant_skill']
    app.applicant_location = request.form['applicant_location']

    db.session.commit()
    return redirect(url_for('workerprofile'))


from sqlalchemy.exc import IntegrityError
from datetime import datetime

@app.route("/worker/update-profile", methods=["POST"])
def update_worker_profile():
    if session.get("user_type") != "worker":
        return jsonify(success=False, message="Unauthorized")

    worker = Worker.query.get(session["worker_id"])
    if not worker:
        return jsonify(success=False, message="Worker not found")

    email = request.form.get("email")
    phone = request.form.get("phone")
    gender = request.form.get("gender")
    dob = request.form.get("dob")
    address = request.form.get("address")
    languages = request.form.getlist("languages")

    # phone uniqueness
    if phone != worker.phone_no:
        if Worker.query.filter_by(phone_no=phone).first():
            return jsonify(success=False, message="Phone already in use")
        worker.phone_no = phone

    # email uniqueness
    if email and email != worker.email:
        if Worker.query.filter_by(email=email).first():
            return jsonify(success=False, message="Email already in use")
        worker.email = email

    worker.gender = gender or None
    worker.address = address or None

    if dob:
        worker.dob = datetime.strptime(dob, "%Y-%m-%d").date()

    allowed = {"Hindi", "English", "Marathi"}
    languages = [l for l in languages if l in allowed]
    worker.languages = ",".join(languages) if languages else None

    try:
        db.session.commit()
    except IntegrityError:
        db.session.rollback()
        return jsonify(success=False, message="Database error")

    return jsonify(success=True)

@app.route("/worker/upload-profile-photo", methods=["POST"])
def upload_profile_photo():
    worker_id = session.get("worker_id")
    if not worker_id:
        return redirect(url_for('auth_bp.login'))

    file = request.files.get("profile_photo")
    if not file or file.filename == "":
        return redirect(url_for("workerprofile"))

    filename = secure_filename(file.filename)
    path = os.path.join("static/uploads", filename)
    file.save(path)

    worker = Worker.query.get(worker_id)
    worker.profile_photo = filename
    db.session.commit()

    return redirect(url_for("workerprofile"))

@app.route("/worker/upload-documents", methods=["POST"])
def upload_worker_documents():
    if session.get("user_type") != "worker":
        return redirect(url_for("logintype"))

    worker = Worker.query.get(session.get("worker_id"))
    if not worker:
        return redirect(url_for("logintype"))

    upload_folder = "static/uploads"
    os.makedirs(upload_folder, exist_ok=True)

    # -------- AADHAR --------
    aadhar = request.files.get("aadhar_card")
    if aadhar and aadhar.filename:
        aadhar_filename = f"{uuid.uuid4()}_{secure_filename(aadhar.filename)}"
        aadhar.save(os.path.join(upload_folder, aadhar_filename))
        worker.aadhar_card = aadhar_filename

    # -------- PAN --------
    pan = request.files.get("pan_card")
    if pan and pan.filename:
        pan_filename = f"{uuid.uuid4()}_{secure_filename(pan.filename)}"
        pan.save(os.path.join(upload_folder, pan_filename))
        worker.pan_card = pan_filename

    # -------- RESUME --------
    resume = request.files.get("resume")
    if resume and resume.filename:
        resume_filename = f"{uuid.uuid4()}_{secure_filename(resume.filename)}"
        resume.save(os.path.join(upload_folder, resume_filename))
        worker.resume = resume_filename

    # -------- KYC STATUS --------
    if worker.aadhar_card and worker.pan_card:
        worker.kyc_status = "submitted"
        session.pop("kyc_started", None)

    db.session.commit()
    flash("Document uploaded successfully.", "success")

    return redirect(url_for("workerprofile"))

@app.route("/worker/start-kyc")
def start_kyc():
    session["kyc_started"] = True
    return "", 204

@app.route("/worker/add-experience", methods=["POST"])
def add_experience():
    if session.get("user_type") != "worker":
        return jsonify(success=False)

    start_date = datetime.strptime(
        request.form["start_date"], "%Y-%m-%d"
    ).date()

    end_date_raw = request.form.get("end_date")
    end_date = (
        datetime.strptime(end_date_raw, "%Y-%m-%d").date()
        if end_date_raw else None
    )

    exp = WorkExperience(
        worker_id=session["worker_id"],
        job_title=request.form["job_title"],
        company_name=request.form["company_name"],
        location=request.form.get("location"),
        start_date=start_date,
        end_date=end_date,
        description=request.form.get("description")
    )

    db.session.add(exp)
    db.session.commit()

    return jsonify(success=True)


@app.route("/worker/add-certification", methods=["POST"])
def add_certification():
    worker_id = session.get("worker_id")
    if not worker_id:
        return redirect(url_for('auth_bp.login'))

    title = request.form.get("title")
    issuer = request.form.get("issuer")

    valid_till_raw = request.form.get("valid_till")
    valid_till = None
    if valid_till_raw:
        valid_till = datetime.strptime(valid_till_raw, "%Y-%m-%d").date()

    file = request.files.get("certificate_file")
    filename = None
    if file and file.filename:
        filename = secure_filename(file.filename)
        file.save(os.path.join("static/uploads", filename))

    cert = Certification(
        worker_id=worker_id,
        title=title,
        issuer=issuer,
        valid_till=valid_till,
        certificate_file=filename
    )

    db.session.add(cert)
    db.session.commit()

    return redirect(url_for("workerprofile"))

from datetime import datetime

@app.route("/worker/add-education", methods=["POST"])
def add_education():
    worker_id = session.get("worker_id")

    if not worker_id:
        return jsonify({"success": False, "message": "Not logged in"})

    edu = Education(
        worker_id=worker_id,
        degree=request.form.get("degree"),
        institution=request.form.get("institution"),
        board_university=request.form.get("board_university"),
        year_of_passing=request.form.get("year_of_passing") or None,
        grade=request.form.get("grade")
    )

    db.session.add(edu)
    db.session.commit()

    return jsonify({"success": True})

# ========================= COMPANY ================================
@app.route("/signup/company", methods=["POST"])
def signup_company():
    if request.method == "GET":
        return render_template("signup.html")

    company_name = request.form.get("company_name")
    email = request.form.get("email")
    password = request.form.get("password")

    if not all([email, password, company_name]):
        return "All required fields must be filled", 400

    existing_company = Company.query.filter_by(email=email).first()
    if existing_company:
        return "Company already registered with this email", 400

    company = Company(
        email=email,
        password=password,
        company_name=company_name
    )

    db.session.add(company)
    db.session.commit()

    session.clear()
    session["company_id"] = company.id
    session["user_type"] = "company"

    return redirect(url_for("companyprofile"))

@app.route("/company-profile")
def companyprofile():
    if session.get("user_type") != "company":
        return redirect(url_for('auth_bp.login'))

    company = Company.query.get(session["company_id"])
    sell_items = sellitem.query.filter_by(
        company_id=company.id
    ).order_by(sellitem.created_at.desc()).all()

    initial = company.company_name[0].upper() if company.company_name else "U"

    return render_template(
        "companyprofile.html",
        company=company,
        initial=initial,
        sell_items=sell_items
    )

@app.route("/company/upload-profile-photo", methods=["POST"])
def upload_company_photo():
    company_id = session.get("company_id")
    if not company_id:
        return redirect(url_for('auth_bp.login'))

    file = request.files.get("profile_photo")
    if not file or file.filename == "":
        return redirect(url_for("companyprofile"))

    filename = secure_filename(file.filename)
    path = os.path.join("static/uploads", filename)
    file.save(path)

    company = Company.query.get(company_id)
    company.profile_photo = filename
    db.session.commit()

    return redirect(url_for("companyprofile"))


@app.route("/company/update-profile", methods=["POST"])
def update_company_profile():
    if session.get("user_type") != "company":
        return jsonify(success=False, message="Unauthorized")

    company = Company.query.get(session["company_id"])
    if not company:
        return jsonify(success=False, message="Company not found")

    company.company_category = request.form.get("company_category") or None
    company.company_city = request.form.get("company_city") or None
    company.company_size = request.form.get("company_size") or None
    company.founded_year = request.form.get("founded_year") or None
    company.gst_number = request.form.get("gst_number") or None

    db.session.commit()
    return jsonify(success=True)


@app.route("/company/update-contact", methods=["POST"])
def update_company_contact():
    if session.get("user_type") != "company":
        return jsonify(success=False, message="Unauthorized")

    company = Company.query.get(session["company_id"])
    if not company:
        return jsonify(success=False, message="Company not found")

    company.phone = request.form.get("phone") or None
    company.website = request.form.get("website") or None
    company.address = request.form.get("address") or None
    company.contact_person = request.form.get("contact_person") or None
    company.contact_designation = request.form.get("contact_designation") or None

    db.session.commit()
    return jsonify(success=True)

# ========================= JOB POST ==========================
@app.route("/company/job", methods=["POST"])
def create_or_edit_job():
    if session.get("user_type") != "company":
        return redirect(url_for('auth_bp.login'))

    job_id = request.form.get("job_id")

    # -------- Job Type --------
    job_type = request.form.get("job_type")
    if job_type == "Other":
        job_type = request.form.get("job_type_other")

    # -------- Shift --------
    shift = request.form.get("shift")
    if shift == "Other":
        shift = request.form.get("shift_other")

    # -------- Convert TIME --------
    job_start_time = datetime.strptime(
        request.form.get("job_start_time"), "%H:%M"
    ).time()

    job_end_time = datetime.strptime(
        request.form.get("job_end_time"), "%H:%M"
    ).time()

    if job_id:
        # ===== EDIT JOB =====
        job = JobPost.query.get(job_id)

        job.job_title = request.form.get("job_title")
        job.job_type = job_type
        job.city = request.form.get("city")
        job.specific_location = request.form.get("specific_location")
        job.shift = shift
        job.job_start_time = job_start_time
        job.job_end_time = job_end_time
        job.job_opening_no = int(request.form.get("job_opening_no"))
        job.salary = request.form.get("salary")
        job.description = request.form.get("description")
        job.job_contact = request.form.get("job_contact")

    else:
        # ===== CREATE JOB =====
        job = JobPost(
            company_id=session["company_id"],
            job_title=request.form.get("job_title"),
            job_type=job_type,
            city=request.form.get("city"),
            specific_location=request.form.get("specific_location"),
            shift=shift,
            job_start_time=job_start_time,
            job_end_time=job_end_time,
            job_opening_no=int(request.form.get("job_opening_no")),
            salary=request.form.get("salary"),
            description=request.form.get("description"),
            job_contact=request.form.get("job_contact"),
        )

        db.session.add(job)

    db.session.commit()
    return redirect(url_for("companyprofile"))

@app.route("/trade/apply", methods=["POST"])
def apply_trade():
    user_type = session.get("user_type")

    if user_type not in ["company", "worker"]:
        flash("Please login to apply for trade", "danger")
        return redirect(url_for('auth_bp.login'))

    buyer_id = session.get("worker_id") if user_type == "worker" else session.get("company_id")

    sell_id = int(request.form.get("sell_id"))
    sell = sellitem.query.get_or_404(sell_id)

    if user_type == "company" and sell.company_id == buyer_id:
        flash("You cannot apply to your own product", "danger")
        return redirect(request.referrer)

    quantity = request.form.get("quantity")
    expected_price = request.form.get("expected_price")
    message = request.form.get("message")

    if not quantity:
        flash("Quantity is required", "danger")
        return redirect(request.referrer)

    existing = TradeRequest.query.filter_by(
        sell_id=sell_id,
        buyer_id=buyer_id,
        buyer_type=user_type,
        status="pending"
    ).first()

    if existing:
        flash("You already sent a request for this product", "warning")
        return redirect(request.referrer)

    trade_request = TradeRequest(
        sell_id=sell_id,
        buyer_id=buyer_id,
        buyer_type=user_type,
        quantity=int(quantity),
        expected_price=float(expected_price) if expected_price else None,
        message=message
    )

    db.session.add(trade_request)
    db.session.commit()

    flash("Trade request sent successfully!", "success")
    return redirect(request.referrer)


@app.route("/apply", methods=["POST"])
def applyjob():
    if session.get("user_type") != "worker":
        return redirect(url_for('auth_bp.login'))

    worker_id = session.get("worker_id")
    worker = Worker.query.get_or_404(worker_id)

    job_id = request.form.get("job_id")
    if not job_id:
        abort(400, "Job ID missing")

    existing = Application.query.filter_by(
        job_id=job_id,
        worker_id=worker_id
    ).first()

    if existing:
        flash("You have already applied for this job", "warning")
        return redirect(url_for("jobvisit", job_id=job_id))

    application = Application(
        job_id=job_id,
        applicant_name=request.form.get("applicant_name"),
        applicant_email=request.form.get("applicant_email"),
        applicant_phone=request.form.get("applicant_phone"),
        applicant_age=request.form.get("applicant_age"),
        applicant_gender=request.form.get("applicant_gender"),
        applicant_skill=request.form.get("applicant_skill"),
        applicant_location=request.form.get("applicant_location"),
        worker_id=worker_id,
        aadhar_card=worker.aadhar_card,
        pan_card=worker.pan_card,
        resume=worker.resume
    )

    db.session.add(application)
    db.session.commit()

    flash("Application submitted successfully!", "success")
    return redirect(url_for("jobvisit", job_id=job_id))


# ========================= TRADE =============================
UPLOAD_FOLDER = "static/uploads/sell_items"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/company/additem", methods=["GET", "POST"])
def add_selling_item():

    if session.get("user_type") != "company":
        return redirect(url_for("home"))

    if request.method == "POST":
        sell_name = request.form.get("sell_name")
        sell_category = request.form.get("sell_category")
        sell_quantity_raw = request.form.get("sell_quantity")
        sell_location = request.form.get("sell_location")
        sell_price_raw = request.form.get("sell_price")
        sell_description = request.form.get("sell_description")

        files = request.files.getlist("sell_images[]")

        if not all([sell_name, sell_quantity_raw, sell_price_raw, sell_description]):
            return "All required fields must be filled", 400

        price_match = re.search(r'[\d.]+', sell_price_raw.replace(',', ''))
        if not price_match:
            return "Invalid price format", 400
        sell_price = float(price_match.group())

        qty_match = re.search(r'\d+', sell_quantity_raw)
        if not qty_match:
            return "Invalid quantity format", 400
        sell_quantity = int(qty_match.group())

        image_filenames = []

        for file in files:
            if file and file.filename != "" and allowed_file(file.filename):
                ext = os.path.splitext(file.filename)[1]
                filename = f"{uuid.uuid4().hex}{ext}"
                file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_filenames.append(filename)

        sell_id = request.form.get("sell_id")
        if sell_id:
            sell = sellitem.query.get(sell_id)

            if sell.company_id != session["company_id"]:
                abort(403)

            sell.sell_name = request.form.get("sell_name") or sell_name
            sell.sell_category = request.form.get("sell_category") or sell_category
            sell.sell_quantity = request.form.get("sell_quantity") or sell_quantity
            sell.sell_price = request.form.get("sell_price") or sell_price
            sell.sell_description = request.form.get("sell_description") or sell_description

        else:
            sell_item = sellitem(
                sell_name=sell_name,
                company_id=session["company_id"],
                sell_category=sell_category or "General",
                sell_quantity=sell_quantity,
                sell_price=sell_price,
                sell_description=sell_description,
                sell_image=json.dumps(image_filenames),
                created_at=datetime.utcnow()
            )

            db.session.add(sell_item)
        db.session.commit()

    return redirect(url_for("companyprofile"))


@app.route('/signup')
def signup():
    return render_template("signup.html")

# ===================== LOGOUT =====================

# ===================== DATABASE INITIALIZATION =====================
with app.app_context():
    db.create_all()
    print("Database tables created/verified successfully!")

@app.route("/api/map/external-jobs")
def api_map_external_jobs():
    """
    Serve Adzuna jobs from DB
    """
    skip_radius  = request.args.get("skip_radius", "0") == "1"
    user_keyword = request.args.get("q", "").strip().lower()

    # Only parse location if radius filtering is needed
    user_lat, user_lng, radius_km = 18.5204, 73.8567, 60.0
    filter_by_location = False
    if not skip_radius:
        try:
            user_lat  = float(request.args.get("lat"))
            user_lng  = float(request.args.get("lng"))
            radius_km = float(request.args.get("radius", 60000)) / 1000
            filter_by_location = True
        except (TypeError, ValueError):
            filter_by_location = False

    jobs_query = AdzunaJob.query.filter_by(active=True)
    all_jobs = jobs_query.all()

    job_list = []
    for job in all_jobs:
        if user_keyword:
            text = f"{job.title} {job.company_name} {job.location_display} {job.description}".lower()
            if not all(w in text for w in user_keyword.split()):
                continue

        if filter_by_location and job.latitude and job.longitude:
            dist = haversine_km(user_lat, user_lng, job.latitude, job.longitude)
            if dist > radius_km:
                continue

        # Re-use existing format for frontend map markers
        job_list.append({
            "id": job.id,
            "title": job.title,
            "company": job.company_name,
            "city": job.location_display,
            "location": job.location_area,
            "salary": f"₹{job.salary_min}-{job.salary_max}" if job.salary_min else "Not disclosed",
            "type": job.contract_type or "Full-time",
            "shift": "",
            "description": (job.description or "")[:200],
            "source": "adzuna",
            "url": job.redirect_url,
            "lat": job.latitude,
            "lng": job.longitude,
        })

    return jsonify(job_list)


@app.route("/api/scraper/status")
def scraper_status():
    """Returns DB info."""
    count = AdzunaJob.query.filter_by(active=True).count()
    return jsonify({
        "cached_jobs": count,
        "last_updated": datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        "cache_file": "db",
    })

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
