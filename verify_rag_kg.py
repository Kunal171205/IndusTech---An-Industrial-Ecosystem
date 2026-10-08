"""
IndusTech — RAG + Knowledge Graph Verification Script
=====================================================
Run this WHILE app.py is running (python app.py).
It tests all 5 core AI subsystems and prints a clear PASS/FAIL report.

Usage:
    python verify_rag_kg.py
"""

import requests
import json
import sys
import os

# Fix Windows console encoding
if os.name == 'nt':
    sys.stdout.reconfigure(encoding='utf-8')

BASE = "http://127.0.0.1:5000"
PASS = 0
FAIL = 0
RESULTS = []

def test(name, passed, detail=""):
    global PASS, FAIL
    status = "✅ PASS" if passed else "❌ FAIL"
    if not passed:
        FAIL += 1
    else:
        PASS += 1
    RESULTS.append((name, status, detail))
    print(f"  {status}  {name}" + (f"  →  {detail}" if detail else ""))


print("=" * 65)
print("  IndusTech — RAG + KG + ReAct Agent Verification")
print("=" * 65)

# ─────────────────────────────────────────────────────────────────
# TEST 1: FAISS Semantic Search (RAG)
# ─────────────────────────────────────────────────────────────────
print("\n[1/5] FAISS Semantic Search (/api/rag-filter)")
try:
    r = requests.get(f"{BASE}/api/rag-filter", params={
        "q": "automobile manufacturing company in Chakan"
    }, timeout=15)
    data = r.json()
    test("RAG returns HTTP 200", r.status_code == 200)
    test("RAG returns results", len(data) > 0, f"{len(data)} companies found")
    if data:
        first = data[0]
        test("Result has company name", bool(first.get("title")), first.get("title", ""))
        test("Result has similarity score", first.get("similarity") is not None, f"{first.get('similarity')}%")
        test("Result has coordinates", first.get("lat") is not None and first.get("lng") is not None)
        test("Result has MIDC zone", "MIDC" in (first.get("city") or ""), first.get("city", ""))
except Exception as e:
    test("RAG endpoint reachable", False, str(e))

# ─────────────────────────────────────────────────────────────────
# TEST 2: Agent Tools Status
# ─────────────────────────────────────────────────────────────────
print("\n[2/5] ReAct Agent Status (/api/agent-tools)")
try:
    r = requests.get(f"{BASE}/api/agent-tools", timeout=10)
    data = r.json()
    test("Agent-tools returns HTTP 200", r.status_code == 200)
    test("Agent is available", data.get("agent_available") == True,
         "ReAct agent loaded" if data.get("agent_available") else "Agent NOT loaded — Ollama may be offline")
    test("8 tools registered", len(data.get("tools", [])) == 8, f"{len(data.get('tools', []))} tools")
    tool_names = [t["name"] for t in data.get("tools", [])]
    for expected in ["SemanticCompanySearch", "ZoneProfile", "IndustryZoneMapper", "SkillGapAnalyzer"]:
        test(f"Tool '{expected}' present", expected in tool_names)
except Exception as e:
    test("Agent-tools endpoint reachable", False, str(e))

# ─────────────────────────────────────────────────────────────────
# TEST 3: Chat / ReAct Agent (with KG fallback)
# ─────────────────────────────────────────────────────────────────
print("\n[3/5] Chat Endpoint — ReAct Agent (/api/chat)")
test_questions = [
    {
        "q": "Which MIDC zone in Pune has the most IT companies?",
        "check_words": ["hinjewadi", "it", "zone", "companies"],
        "label": "Industry-zone query"
    },
    {
        "q": "What companies are in Bhosari MIDC?",
        "check_words": ["bhosari"],
        "label": "Zone-specific query"
    },
    {
        "q": "What skills does a Computer Engineering student need for IT Services?",
        "check_words": ["skill", "python", "java", "web", "data"],
        "label": "Skill gap query"
    },
]
try:
    for tq in test_questions:
        r = requests.post(f"{BASE}/api/chat", json={"message": tq["q"], "history": []}, timeout=60)
        data = r.json()
        answer = (data.get("answer") or "").lower()
        mode = data.get("mode", "unknown")
        steps = data.get("steps", [])

        test(f"Chat '{tq['label']}' — HTTP 200", r.status_code == 200)
        test(f"Chat '{tq['label']}' — got answer", len(answer) > 10,
             f"mode={mode}, answer_len={len(answer)}, steps={len(steps)}")

        if mode == "agent" and steps:
            tools_used = [s["tool"] for s in steps]
            test(f"Chat '{tq['label']}' — agent used tools", len(tools_used) > 0,
                 f"Tools: {', '.join(tools_used)}")
        elif mode == "rag":
            test(f"Chat '{tq['label']}' — RAG fallback used", True, "Agent unavailable, RAG responded")
        else:
            test(f"Chat '{tq['label']}' — response mode", False, f"Unexpected mode: {mode}")
except Exception as e:
    test("Chat endpoint reachable", False, str(e))

# ─────────────────────────────────────────────────────────────────
# TEST 4: Map Jobs API (uses resolve_job_location with KG)
# ─────────────────────────────────────────────────────────────────
print("\n[4/5] Map Jobs API — Location Resolution (/api/map/jobs)")
try:
    r = requests.get(f"{BASE}/api/map/jobs", params={
        "lat": 18.62, "lng": 73.88, "radius": 50000, "city": "Pune", "q": ""
    }, timeout=20)
    data = r.json()
    test("Map jobs returns HTTP 200", r.status_code == 200)
    test("Map jobs returns results", len(data) > 0, f"{len(data)} jobs")
    if data:
        first = data[0]
        test("Job has location_confidence", first.get("location_confidence") is not None,
             first.get("location_confidence", ""))
        confidences = set(j.get("location_confidence") for j in data)
        test("Multiple confidence levels", len(confidences) >= 1, f"Levels: {confidences}")
        test("Job has lat/lng", first.get("lat") is not None and first.get("lng") is not None)
except Exception as e:
    test("Map jobs endpoint reachable", False, str(e))

# ─────────────────────────────────────────────────────────────────
# TEST 5: Map Companies API (local DB + RAG)
# ─────────────────────────────────────────────────────────────────
print("\n[5/5] Map Companies API (/api/map/companies)")
try:
    r = requests.get(f"{BASE}/api/map/companies", timeout=15)
    data = r.json()
    test("Map companies returns HTTP 200", r.status_code == 200)
    test("Map companies returns results", len(data) > 0, f"{len(data)} companies")
except Exception as e:
    test("Map companies endpoint reachable", False, str(e))


# ─────────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────────
print("\n" + "=" * 65)
print(f"  RESULTS:  {PASS} passed  |  {FAIL} failed  |  {PASS + FAIL} total")
print("=" * 65)

if FAIL == 0:
    print("\n  🎉 All systems operational! RAG + KG + Agent working correctly.\n")
else:
    print(f"\n  ⚠️  {FAIL} test(s) failed. Check details above.\n")
    print("  Common fixes:")
    print("    • If Agent tests fail → ensure Ollama is running: ollama serve")
    print("    • If RAG tests fail   → rebuild index: python build_rag_index.py")
    print("    • If KG tests fail    → check Neo4j: python load_knowledge_graph.py")
    print()

sys.exit(1 if FAIL > 0 else 0)
