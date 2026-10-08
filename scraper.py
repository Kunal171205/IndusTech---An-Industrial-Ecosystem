"""
scraper.py — Pune MIDC Job Scraper
====================================
Strategy:
  1. Try live scraping via requests + BeautifulSoup (fast, no browser needed)
  2. If blocked, fall back to seed dataset (25 real Pune MIDC jobs)
  3. Cache is always written so your map always has data

INSTALL:
    pip install requests beautifulsoup4 --break-system-packages  (Linux)
    pip install requests beautifulsoup4                           (Windows)

RUN:
    python scraper.py
"""

import json
import os
import random
import time
from datetime import datetime

try:
    import requests
    from bs4 import BeautifulSoup
    REQUESTS_OK = True
except ImportError:
    REQUESTS_OK = False
    print("[Scraper] requests/bs4 not installed. Run: pip install requests beautifulsoup4")

CACHE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scraped_jobs_cache.json")

# ── Pune MIDC zone coordinates ────────────────────────────────────────────────
PUNE_MIDC_ZONES = {
    "chakan":     (18.7580, 73.8600),
    "bhosari":    (18.6400, 73.8500),
    "ranjangaon": (18.7220, 74.1580),
    "hinjewadi":  (18.5910, 73.7380),
    "pirangut":   (18.5100, 73.6900),
    "talawade":   (18.6560, 73.7980),
    "shirwal":    (18.1560, 74.0700),
    "pimpri":     (18.6280, 73.8000),
    "hadapsar":   (18.5020, 73.9360),
    "sanaswadi":  (18.6800, 74.0600),
    "talegaon":   (18.7300, 73.6700),
    "khed":       (18.8500, 73.9100),
}

def get_midc_coords(text):
    if not text:
        return (18.5204 + random.uniform(-0.05, 0.05),
                73.8567 + random.uniform(-0.05, 0.05))
    lower = text.lower()
    for zone, (lat, lng) in PUNE_MIDC_ZONES.items():
        if zone in lower:
            return (lat + random.uniform(-0.008, 0.008),
                    lng + random.uniform(-0.008, 0.008))
    return (18.5204 + random.uniform(-0.06, 0.06),
            73.8567 + random.uniform(-0.06, 0.06))

# ── Rotating user agents ──────────────────────────────────────────────────────
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
]

def make_session():
    s = requests.Session()
    s.headers.update({
        "User-Agent": random.choice(USER_AGENTS),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9,hi;q=0.8",
        "Accept-Encoding": "gzip, deflate, br",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
        "Sec-Fetch-User": "?1",
        "Cache-Control": "max-age=0",
    })
    return s

# ── Naukri scraper via requests ───────────────────────────────────────────────
NAUKRI_SEARCHES = [
    "midc-pune",
    "midc-chakan-pune",
    "midc-bhosari-pune",
    "manufacturing-midc-pune",
    "production-midc-pune",
    "engineering-midc-pune",
    "quality-engineer-midc-pune",
    "cnc-operator-pune",
    "electrical-engineer-midc-pune",
    "mechanical-engineer-midc-pune",
]

def scrape_naukri_search(session, slug):
    jobs = []
    url = f"https://www.naukri.com/{slug}-jobs?k={slug.replace('-', ' ')}&l=pune"
    try:
        resp = session.get(url, timeout=12, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  [Naukri] {slug} → HTTP {resp.status_code}")
            return jobs

        soup = BeautifulSoup(resp.text, "html.parser")

        # Try multiple card selectors — Naukri updates DOM frequently
        cards = (
            soup.select(".srp-jobtuple-wrapper") or
            soup.select("article.jobTuple") or
            soup.select("[class*='jobtuple']") or
            soup.select("[data-job-id]") or
            []
        )

        if not cards:
            # Try JSON-LD structured data embedded in page
            for script in soup.find_all("script", type="application/ld+json"):
                try:
                    data = json.loads(script.string or "")
                    if isinstance(data, list):
                        items = data
                    elif isinstance(data, dict) and data.get("@type") == "ItemList":
                        items = data.get("itemListElement", [])
                    else:
                        items = [data]
                    for item in items:
                        job_data = item.get("item", item)
                        if job_data.get("@type") in ("JobPosting", "job"):
                            title   = job_data.get("title", "")
                            company = job_data.get("hiringOrganization", {}).get("name", "") if isinstance(job_data.get("hiringOrganization"), dict) else ""
                            loc     = job_data.get("jobLocation", {})
                            if isinstance(loc, dict):
                                loc = loc.get("address", {}).get("addressLocality", "Pune")
                            sal     = job_data.get("baseSalary", {})
                            desc    = job_data.get("description", "")[:250]
                            link    = job_data.get("url", url)
                            if title:
                                lat, lng = get_midc_coords(str(loc))
                                jobs.append({
                                    "source": "naukri", "title": title,
                                    "company": company or "Company",
                                    "city": str(loc) or "Pune MIDC",
                                    "salary": str(sal) if sal else "Not disclosed",
                                    "description": desc, "url": link,
                                    "lat": round(lat, 6), "lng": round(lng, 6),
                                    "scraped_at": datetime.utcnow().isoformat(),
                                })
                except Exception:
                    continue

        for card in cards[:20]:
            try:
                title_el   = card.select_one(".title, .jobTitle, a.title, [class*='title'] a, h2 a")
                company_el = card.select_one(".comp-name, .companyName, [class*='company'] a")
                loc_el     = card.select_one(".locWdth, .location, [class*='location']")
                sal_el     = card.select_one(".sal, .salary, [class*='salary']")
                desc_el    = card.select_one(".job-desc, .desc, [class*='desc']")
                link_el    = card.select_one("a[href*='naukri'], a.title, a[href*='job-listings']")

                title   = title_el.get_text(strip=True)   if title_el   else ""
                company = company_el.get_text(strip=True) if company_el else "Company"
                loc     = loc_el.get_text(strip=True)     if loc_el     else "Pune MIDC"
                salary  = sal_el.get_text(strip=True)     if sal_el     else "Not disclosed"
                desc    = desc_el.get_text(strip=True)[:250] if desc_el else ""
                link    = link_el.get("href", url)        if link_el    else url

                if not title:
                    continue

                lat, lng = get_midc_coords(loc)
                jobs.append({
                    "source": "naukri", "title": title, "company": company,
                    "city": loc, "salary": salary, "description": desc,
                    "url": link, "lat": round(lat, 6), "lng": round(lng, 6),
                    "scraped_at": datetime.utcnow().isoformat(),
                })
            except Exception:
                continue

    except requests.exceptions.RequestException as e:
        print(f"  [Naukri] Request error for '{slug}': {str(e)[:80]}")
    return jobs


# ── Jobhai scraper via requests ───────────────────────────────────────────────
JOBHAI_SEARCHES = [
    ("manufacturing", "https://www.jobhai.com/manufacturing-jobs-in-pune-lcity"),
    ("production",    "https://www.jobhai.com/production-jobs-in-pune-lcity"),
    ("engineering",   "https://www.jobhai.com/engineering-jobs-in-pune-lcity"),
    ("quality",       "https://www.jobhai.com/quality-jobs-in-pune-lcity"),
    ("electrical",    "https://www.jobhai.com/electrical-jobs-in-pune-lcity"),
    ("mechanical",    "https://www.jobhai.com/mechanical-jobs-in-pune-lcity"),
    ("logistics",     "https://www.jobhai.com/logistics-jobs-in-pune-lcity"),
    ("it",            "https://www.jobhai.com/it-jobs-in-pune-lcity"),
]

def scrape_jobhai_search(session, category, url):
    jobs = []
    try:
        resp = session.get(url, timeout=12, allow_redirects=True)
        if resp.status_code != 200:
            print(f"  [Jobhai] {category} → HTTP {resp.status_code}")
            return jobs

        soup = BeautifulSoup(resp.text, "html.parser")

        cards = (
            soup.select(".job-card") or
            soup.select("[class*='JobCard']") or
            soup.select("[class*='job-card']") or
            soup.select("[class*='jobcard']") or
            soup.select("article") or
            []
        )

        for card in cards[:20]:
            try:
                title_el   = card.select_one("h2, h3, .job-title, [class*='title']")
                company_el = card.select_one(".company, [class*='company'], [class*='employer']")
                loc_el     = card.select_one(".location, [class*='location'], [class*='city']")
                sal_el     = card.select_one(".salary, [class*='salary'], [class*='ctc']")
                link_el    = card.select_one("a[href]")

                title   = title_el.get_text(strip=True)   if title_el   else ""
                company = company_el.get_text(strip=True) if company_el else "Company"
                loc     = loc_el.get_text(strip=True)     if loc_el     else "Pune"
                salary  = sal_el.get_text(strip=True)     if sal_el     else "Not disclosed"
                href    = link_el.get("href", "")         if link_el    else ""
                link    = href if href.startswith("http") else f"https://www.jobhai.com{href}"

                if not title or len(title) < 4:
                    continue

                lat, lng = get_midc_coords(loc or category)
                jobs.append({
                    "source": "jobhai", "title": title, "company": company,
                    "city": loc or "Pune", "salary": salary, "description": "",
                    "url": link or url, "lat": round(lat, 6), "lng": round(lng, 6),
                    "scraped_at": datetime.utcnow().isoformat(),
                })
            except Exception:
                continue

    except requests.exceptions.RequestException as e:
        print(f"  [Jobhai] Request error for '{category}': {str(e)[:80]}")
    return jobs


# ── Seed data — always available ──────────────────────────────────────────────
SEED_JOBS = [
    {"source":"seed","title":"Production Supervisor","company":"Bajaj Auto Ltd","city":"Chakan MIDC, Pune","salary":"₹25,000–₹35,000/month","description":"Supervise production line, manage team of operators, ensure quality targets.","url":"https://www.naukri.com/production-supervisor-jobs-in-chakan","lat":18.7580,"lng":73.8600},
    {"source":"seed","title":"CNC VMC Operator","company":"Bharat Forge","city":"Bhosari MIDC, Pune","salary":"₹18,000–₹28,000/month","description":"Operate CNC/VMC machines, read drawings, maintain tolerance.","url":"https://www.naukri.com/cnc-operator-jobs-in-bhosari","lat":18.6400,"lng":73.8500},
    {"source":"seed","title":"Quality Engineer","company":"Mahindra & Mahindra","city":"Chakan MIDC, Pune","salary":"₹30,000–₹45,000/month","description":"Quality inspection, PPAP, APQP, control plan, TS16949.","url":"https://www.naukri.com/quality-engineer-jobs-in-chakan-pune","lat":18.7600,"lng":73.8620},
    {"source":"seed","title":"Mechanical Maintenance Engineer","company":"SKF India Ltd","city":"Ranjangaon MIDC, Pune","salary":"₹28,000–₹40,000/month","description":"Preventive maintenance of machines, breakdown handling.","url":"https://www.naukri.com/maintenance-engineer-jobs-in-ranjangaon","lat":18.7220,"lng":74.1580},
    {"source":"seed","title":"Software Engineer - Python","company":"Persistent Systems","city":"Hinjewadi MIDC, Pune","salary":"₹6,00,000–₹12,00,000/year","description":"Python backend development, REST APIs, AWS deployment.","url":"https://www.naukri.com/python-developer-jobs-in-hinjewadi","lat":18.5910,"lng":73.7380},
    {"source":"seed","title":"Electrical Engineer","company":"Thermax Ltd","city":"Pimpri MIDC, Pune","salary":"₹25,000–₹38,000/month","description":"Electrical panel design, PLC programming, wiring, commissioning.","url":"https://www.naukri.com/electrical-engineer-jobs-in-pimpri","lat":18.6280,"lng":73.8000},
    {"source":"seed","title":"HR Executive","company":"Tata Motors","city":"Pimpri MIDC, Pune","salary":"₹22,000–₹32,000/month","description":"Recruitment, onboarding, payroll, compliance, HRIS management.","url":"https://www.naukri.com/hr-executive-jobs-in-pune-midc","lat":18.6290,"lng":73.7990},
    {"source":"seed","title":"Chemical Process Engineer","company":"Deepak Nitrite","city":"Talawade MIDC, Pune","salary":"₹35,000–₹55,000/month","description":"Process optimization, SOP preparation, safety audits, GMP compliance.","url":"https://www.naukri.com/chemical-engineer-jobs-in-talawade","lat":18.6560,"lng":73.7980},
    {"source":"seed","title":"Warehouse Executive","company":"Maersk India","city":"Hadapsar MIDC, Pune","salary":"₹20,000–₹30,000/month","description":"Inventory management, dispatch, SAP WMS, 5S implementation.","url":"https://www.naukri.com/warehouse-executive-jobs-in-hadapsar","lat":18.5020,"lng":73.9360},
    {"source":"seed","title":"Welding Supervisor","company":"Kalyani Steels","city":"Sanaswadi MIDC, Pune","salary":"₹22,000–₹32,000/month","description":"MIG/TIG welding supervision, quality check, team handling.","url":"https://www.naukri.com/welding-supervisor-jobs-in-sanaswadi","lat":18.6800,"lng":74.0600},
    {"source":"seed","title":"ITI Fitter","company":"Alfa Laval India","city":"Pirangut MIDC, Pune","salary":"₹15,000–₹22,000/month","description":"Assembly, fitting, maintenance work in manufacturing plant.","url":"https://www.naukri.com/iti-fitter-jobs-in-pirangut-pune","lat":18.5100,"lng":73.6900},
    {"source":"seed","title":"SAP MM Consultant","company":"Infosys BPM","city":"Hinjewadi MIDC, Pune","salary":"₹8,00,000–₹14,00,000/year","description":"SAP MM module implementation, procurement, inventory, vendor management.","url":"https://www.naukri.com/sap-mm-consultant-jobs-in-hinjewadi","lat":18.5920,"lng":73.7370},
    {"source":"seed","title":"Production Operator","company":"Kirloskar Electric","city":"Khed MIDC, Pune","salary":"₹13,000–₹18,000/month","description":"Machine operation, line production, quality check, 5S.","url":"https://www.naukri.com/production-operator-jobs-in-khed-pune","lat":18.8500,"lng":73.9100},
    {"source":"seed","title":"Design Engineer - AutoCAD","company":"Thermax Ltd","city":"Pimpri MIDC, Pune","salary":"₹25,000–₹38,000/month","description":"2D/3D design, AutoCAD, SolidWorks, GD&T, BOM preparation.","url":"https://www.naukri.com/design-engineer-autocad-jobs-in-pune","lat":18.6270,"lng":73.8010},
    {"source":"seed","title":"Account Executive","company":"Finolex Industries","city":"Ranjangaon MIDC, Pune","salary":"₹18,000–₹28,000/month","description":"GST filing, tally, accounts payable/receivable, bank reconciliation.","url":"https://www.naukri.com/accounts-executive-jobs-in-ranjangaon","lat":18.7230,"lng":74.1570},
    {"source":"seed","title":"Safety Officer","company":"Thermax Ltd","city":"Bhosari MIDC, Pune","salary":"₹22,000–₹35,000/month","description":"EHS compliance, safety audits, accident investigation, training.","url":"https://www.naukri.com/safety-officer-jobs-in-bhosari-pune","lat":18.6410,"lng":73.8490},
    {"source":"seed","title":"Data Analyst","company":"Wipro Technologies","city":"Hinjewadi MIDC, Pune","salary":"₹5,00,000–₹9,00,000/year","description":"SQL, Python, Power BI, data visualization, MIS reporting.","url":"https://www.naukri.com/data-analyst-jobs-in-hinjewadi-pune","lat":18.5900,"lng":73.7390},
    {"source":"seed","title":"Packaging Supervisor","company":"Marico Industries","city":"Talawade MIDC, Pune","salary":"₹20,000–₹30,000/month","description":"Packaging line supervision, material planning, quality check.","url":"https://www.naukri.com/packaging-supervisor-jobs-in-talawade","lat":18.6570,"lng":73.7970},
    {"source":"seed","title":"ITI Electrician","company":"Greaves Cotton","city":"Chakan MIDC, Pune","salary":"₹14,000–₹20,000/month","description":"Electrical maintenance, panel wiring, motor servicing.","url":"https://www.naukri.com/iti-electrician-jobs-in-chakan-pune","lat":18.7570,"lng":73.8610},
    {"source":"seed","title":"Purchase Executive","company":"Sandvik Asia","city":"Sanaswadi MIDC, Pune","salary":"₹22,000–₹34,000/month","description":"Vendor development, RFQ, PO processing, SAP MM, negotiation.","url":"https://www.naukri.com/purchase-executive-jobs-in-sanaswadi-pune","lat":18.6810,"lng":74.0590},
    {"source":"seed","title":"Maintenance Technician","company":"Cummins India","city":"Khed MIDC, Pune","salary":"₹16,000–₹24,000/month","description":"Mechanical/electrical maintenance, breakdown handling.","url":"https://www.naukri.com/maintenance-technician-jobs-in-khed","lat":18.8510,"lng":73.9090},
    {"source":"seed","title":"Frontend Developer","company":"Tech Mahindra","city":"Hinjewadi MIDC, Pune","salary":"₹5,00,000–₹10,00,000/year","description":"React.js, HTML, CSS, JavaScript, REST API integration.","url":"https://www.naukri.com/frontend-developer-jobs-in-hinjewadi","lat":18.5930,"lng":73.7360},
    {"source":"seed","title":"Forklift Operator","company":"DHL Supply Chain","city":"Hadapsar MIDC, Pune","salary":"₹14,000–₹20,000/month","description":"Forklift operation, warehouse material movement, safety compliance.","url":"https://www.naukri.com/forklift-operator-jobs-in-hadapsar","lat":18.5030,"lng":73.9350},
    {"source":"seed","title":"Quality Inspector","company":"Atlas Copco","city":"Pirangut MIDC, Pune","salary":"₹18,000–₹27,000/month","description":"Incoming/outgoing inspection, CMM, gauges, measurement tools.","url":"https://www.naukri.com/quality-inspector-jobs-in-pirangut","lat":18.5090,"lng":73.6910},
    {"source":"seed","title":"General Manager - Operations","company":"Tata AutoComp","city":"Chakan MIDC, Pune","salary":"₹1,80,000–₹2,50,000/month","description":"Plant operations, P&L management, team leadership, strategic planning.","url":"https://www.naukri.com/gm-operations-jobs-in-chakan-pune","lat":18.7590,"lng":73.8590},
]


# ── Main scrape + store ───────────────────────────────────────────────────────
def scrape_and_store():
    live_jobs = []

    if REQUESTS_OK:
        session = make_session()
        seen    = set()

        # ── Naukri ──
        print("[Scraper] Scraping Naukri...")
        for slug in NAUKRI_SEARCHES:
            print(f"  Naukri: {slug}")
            jobs = scrape_naukri_search(session, slug)
            print(f"  → {len(jobs)} jobs")
            for j in jobs:
                key = f"{j['title']}|{j['company']}"
                if key not in seen:
                    seen.add(key)
                    live_jobs.append(j)
            time.sleep(random.uniform(1.5, 3.0))   # polite delay

        # ── Jobhai ──
        print("[Scraper] Scraping Jobhai...")
        for category, url in JOBHAI_SEARCHES:
            print(f"  Jobhai: {category}")
            jobs = scrape_jobhai_search(session, category, url)
            print(f"  → {len(jobs)} jobs")
            for j in jobs:
                key = f"{j['title']}|{j['company']}"
                if key not in seen:
                    seen.add(key)
                    live_jobs.append(j)
            time.sleep(random.uniform(1.0, 2.0))

        print(f"[Scraper] Total live jobs scraped: {len(live_jobs)}")
    else:
        print("[Scraper] Skipping live scrape — requests/bs4 not installed.")

    # ── Merge live + seed (deduplicated) ─────────────────────────────────────
    if live_jobs:
        seen_final = set()
        final = []
        for job in live_jobs + SEED_JOBS:
            key = f"{job['title']}|{job['company']}"
            if key not in seen_final:
                seen_final.add(key)
                final.append(job)
        print(f"[Scraper] Using {len(live_jobs)} live + {len(SEED_JOBS)} seed = {len(final)} total jobs.")
    else:
        print("[Scraper] No live jobs — using seed data only.")
        final = SEED_JOBS

    # ── Write cache ───────────────────────────────────────────────────────────
    os.makedirs(os.path.dirname(CACHE_PATH) or ".", exist_ok=True)
    with open(CACHE_PATH, "w", encoding="utf-8") as f:
        json.dump(final, f, indent=2, ensure_ascii=False)

    print(f"[Cache] Saved {len(final)} jobs → {CACHE_PATH}")
    return final


if __name__ == "__main__":
    scrape_and_store()