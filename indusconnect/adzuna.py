"""
indusconnect/adzuna.py
======================
Adzuna API client for IndusConnect.

Responsibilities:
  - Fetch jobs from Adzuna India search API
  - Paginate safely (stop on empty results or max pages)
  - Retry with exponential backoff on transient errors
  - Normalize raw Adzuna JSON into canonical job dicts
  - Log structured progress

All credentials read from environment variables — never hardcoded.
"""

import os
import time
import logging
import requests
from typing import Iterator, List, Optional

logger = logging.getLogger("[ADZUNA]")

# ── Environment config ────────────────────────────────────────────────────────
def _cfg(key: str, default: str = "") -> str:
    return os.getenv(key, default)


ADZUNA_BASE   = "https://api.adzuna.com/v1/api"
ADZUNA_COUNTRY = _cfg("ADZUNA_COUNTRY", "in")

# Default search terms for MIDC/industrial Pune jobs
DEFAULT_SEARCH_TERMS = [
    "manufacturing pune",
    "production engineer pune",
    "mechanical engineer pune",
    "electrical engineer pune",
    "quality engineer pune",
    "cnc operator pune",
    "welding pune",
    "fabrication pune",
    "chemical engineer pune",
    "logistics pune",
    "industrial pune",
    "midc pune",
]

# ── Adzuna API client ─────────────────────────────────────────────────────────

class AdzunaClient:
    """
    Thin wrapper around the Adzuna Jobs Search API.

    Usage:
        client = AdzunaClient()
        for job in client.iter_jobs(what="CNC operator", where="Pune"):
            print(job)
    """

    def __init__(
        self,
        app_id: Optional[str] = None,
        app_key: Optional[str] = None,
        country: Optional[str] = None,
        results_per_page: int = 50,
        max_pages: int = 5,
        timeout: int = 15,
        max_retries: int = 3,
    ):
        self.app_id  = app_id  or _cfg("ADZUNA_APP_ID")
        self.app_key = app_key or _cfg("ADZUNA_APP_KEY")
        self.country = country or _cfg("ADZUNA_COUNTRY", "in")
        self.results_per_page = int(_cfg("ADZUNA_RESULTS_PER_PAGE", str(results_per_page)))
        self.max_pages        = int(_cfg("ADZUNA_MAX_PAGES",        str(max_pages)))
        self.timeout          = timeout
        self.max_retries      = max_retries

        if not self.app_id or not self.app_key:
            raise ValueError(
                "ADZUNA_APP_ID and ADZUNA_APP_KEY must be set in environment variables."
            )

    def _fetch_page(self, what: str, where: str, page: int) -> List[dict]:
        """
        Fetch a single page of results from Adzuna.
        Returns the raw 'results' list, or [] on error.
        """
        url = (
            f"{ADZUNA_BASE}/jobs/{self.country}/search/{page}"
            f"?app_id={self.app_id}"
            f"&app_key={self.app_key}"
            f"&results_per_page={self.results_per_page}"
            f"&what={requests.utils.quote(what)}"
            f"&where={requests.utils.quote(where)}"
            f"&sort_by=date"
            f"&content-type=application/json"
        )

        for attempt in range(1, self.max_retries + 1):
            try:
                resp = requests.get(url, timeout=self.timeout)

                if resp.status_code == 200:
                    data = resp.json()
                    results = data.get("results", [])
                    logger.info(
                        f"Page {page} | what='{what}' | "
                        f"received={len(results)} | "
                        f"total_count={data.get('count', '?')}"
                    )
                    return results

                elif resp.status_code == 429:
                    wait = 2 ** attempt
                    logger.warning(f"Rate limited. Waiting {wait}s before retry {attempt}/{self.max_retries}")
                    time.sleep(wait)

                elif resp.status_code in (400, 401, 403):
                    logger.error(f"Adzuna auth/param error {resp.status_code}: {resp.text[:200]}")
                    return []

                else:
                    logger.warning(f"HTTP {resp.status_code} on attempt {attempt}. Retrying...")
                    time.sleep(2 ** attempt)

            except requests.exceptions.Timeout:
                logger.warning(f"Timeout on attempt {attempt}/{self.max_retries}")
                time.sleep(2 ** attempt)

            except requests.exceptions.RequestException as e:
                logger.warning(f"Request error on attempt {attempt}: {e}")
                time.sleep(2 ** attempt)

        logger.error(f"All {self.max_retries} attempts failed for page {page} what='{what}'")
        return []

    def iter_jobs(self, what: str = "", where: str = "Pune") -> Iterator[dict]:
        """
        Iterate over all paginated results for a search query.

        Stops when:
          - A page returns 0 results
          - max_pages is reached

        Yields raw Adzuna job dicts (not yet normalized).
        """
        for page in range(1, self.max_pages + 1):
            results = self._fetch_page(what=what, where=where, page=page)

            if not results:
                logger.info(f"No results on page {page}. Stopping pagination.")
                break

            yield from results

            # Pause between pages to be polite
            if page < self.max_pages:
                time.sleep(0.3)

    def fetch_all_terms(
        self,
        search_terms: Optional[List[str]] = None,
        where: str = "Pune",
    ) -> List[dict]:
        """
        Fetch jobs for multiple search terms, deduplicate by Adzuna job ID.

        Returns a list of raw Adzuna job dicts.
        """
        terms = search_terms or DEFAULT_SEARCH_TERMS
        seen_ids: set = set()
        all_jobs: List[dict] = []

        total_received = 0

        for term in terms:
            logger.info(f"Fetching term: '{term}'")
            for raw_job in self.iter_jobs(what=term, where=where):
                total_received += 1
                jid = str(raw_job.get("id", ""))
                if jid in seen_ids:
                    continue
                seen_ids.add(jid)
                all_jobs.append(raw_job)

        logger.info(
            f"Fetch complete: {total_received} raw jobs received, "
            f"{len(all_jobs)} unique after deduplication"
        )
        return all_jobs


# ── Normalization ─────────────────────────────────────────────────────────────

def normalize_job(raw: dict) -> Optional[dict]:
    """
    Convert a raw Adzuna API result into a canonical job dict.

    Handles missing/null fields defensively — never assumes any field exists.

    Canonical fields produced:
        source, source_job_id, title, description, company_name,
        location_display, location_area, latitude, longitude,
        category_label, category_tag, contract_type, contract_time,
        salary_min, salary_max, salary_is_predicted,
        created_at, redirect_url, raw_source_data

    midc_zone and industry are added later by kg_resolver.
    """
    if not raw:
        return None

    source_job_id = str(raw.get("id", "")).strip()
    if not source_job_id:
        return None

    # Location
    loc      = raw.get("location") or {}
    area     = loc.get("area") or []
    loc_disp = loc.get("display_name") or ""

    # Category
    cat      = raw.get("category") or {}
    cat_lbl  = cat.get("label") or ""
    cat_tag  = cat.get("tag") or ""

    # Company
    co       = raw.get("company") or {}
    co_name  = co.get("display_name") or ""

    # Salary
    sal_min  = raw.get("salary_min")
    sal_max  = raw.get("salary_max")
    sal_pred = raw.get("salary_is_predicted")
    try:
        sal_min = float(sal_min) if sal_min is not None else None
    except (TypeError, ValueError):
        sal_min = None
    try:
        sal_max = float(sal_max) if sal_max is not None else None
    except (TypeError, ValueError):
        sal_max = None

    # Coordinates
    try:
        latitude = float(raw["latitude"]) if raw.get("latitude") else None
    except (TypeError, ValueError):
        latitude = None
    try:
        longitude = float(raw["longitude"]) if raw.get("longitude") else None
    except (TypeError, ValueError):
        longitude = None

    return {
        "source":             "adzuna",
        "source_job_id":      source_job_id,
        "title":              (raw.get("title") or "").strip(),
        "description":        (raw.get("description") or "").strip(),
        "company_name":       co_name.strip(),
        "location_display":   loc_disp.strip(),
        "location_area":      ", ".join(str(a) for a in area),
        "latitude":           latitude,
        "longitude":          longitude,
        "category_label":     cat_lbl.strip(),
        "category_tag":       cat_tag.strip(),
        "contract_type":      (raw.get("contract_type") or "").strip(),
        "contract_time":      (raw.get("contract_time") or "").strip(),
        "salary_min":         sal_min,
        "salary_max":         sal_max,
        "salary_is_predicted": bool(sal_pred) if sal_pred is not None else None,
        "created_at":         (raw.get("created") or "").strip(),
        "redirect_url":       (raw.get("redirect_url") or "").strip(),
        "raw_source_data":    raw,   # preserve full original for debugging
        "midc_zone":          None,  # filled by kg_resolver
        "industry":           None,  # filled by kg_resolver
    }
