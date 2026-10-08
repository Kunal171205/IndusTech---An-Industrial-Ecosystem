"""
indusconnect/kg_resolver.py
============================
Knowledge Graph zone resolution for IndusConnect.

Resolves a job's MIDC zone and industry using Neo4j.

Architecture:
    Company name / Location text
        ↓
    Neo4j (Company → LOCATED_IN → MIDCZone → BELONGS_TO → Industry)
        ↓
    midc_zone (canonical name) | industry

Resolution order:
    1. Exact company name match in KG
    2. Fuzzy company name (CONTAINS) in KG
    3. Location text → known zone name alias
    4. No zone (return None — never invent)

Canonical MIDC zones:
    chakan, bhosari, ranjangaon, hinjewadi, pirangut,
    talawade, shirwal, pimpri, hadapsar, sanaswadi, talegaon, khed
"""

import re
import logging
from typing import Optional, Tuple

logger = logging.getLogger("[KG]")

# ── Canonical zone alias map ──────────────────────────────────────────────────
# Maps common text variants to the canonical zone name stored in Neo4j.
ZONE_ALIASES: dict[str, str] = {
    # Chakan
    "chakan":                   "Chakan",
    "chakan midc":              "Chakan",
    "chakan industrial area":   "Chakan",
    "chakan industrial estate": "Chakan",
    # Bhosari
    "bhosari":                  "Bhosari",
    "bhosari midc":             "Bhosari",
    "bhosari industrial area":  "Bhosari",
    # Ranjangaon
    "ranjangaon":               "Ranjangaon",
    "ranjangaon midc":          "Ranjangaon",
    # Hinjewadi
    "hinjewadi":                "Hinjewadi",
    "hinjewadi midc":           "Hinjewadi",
    "hinjewadi it park":        "Hinjewadi",
    "rajiv gandhi it park":     "Hinjewadi",
    # Pirangut
    "pirangut":                 "Pirangut",
    "pirangut midc":            "Pirangut",
    # Talawade
    "talawade":                 "Talawade",
    "talawade midc":            "Talawade",
    # Shirwal
    "shirwal":                  "Shirwal",
    "shirwal midc":             "Shirwal",
    # Pimpri-Chinchwad
    "pimpri":                   "Pimpri",
    "pimpri midc":              "Pimpri",
    "chinchwad":                "Pimpri",
    "pimpri chinchwad":         "Pimpri",
    "pcmc":                     "Pimpri",
    # Hadapsar
    "hadapsar":                 "Hadapsar",
    "hadapsar midc":            "Hadapsar",
    "hadapsar industrial estate": "Hadapsar",
    # Sanaswadi
    "sanaswadi":                "Sanaswadi",
    "sanaswadi midc":           "Sanaswadi",
    # Talegaon
    "talegaon":                 "Talegaon",
    "talegaon midc":            "Talegaon",
    "talegaon dabhade":         "Talegaon",
    # Khed
    "khed":                     "Khed",
    "khed midc":                "Khed",
    "rajgurunagar":             "Khed",
}

# Pre-sorted by length (longest first) for greedy alias matching
_SORTED_ALIASES = sorted(ZONE_ALIASES.keys(), key=len, reverse=True)


def detect_zone_from_text(text: str) -> Optional[str]:
    """
    Detect a canonical MIDC zone name from a text string.
    Uses alias matching (longest first, case-insensitive).

    Returns the canonical zone name (e.g. "Chakan") or None.
    """
    if not text:
        return None
    lower = text.lower()
    for alias in _SORTED_ALIASES:
        if alias in lower:
            return ZONE_ALIASES[alias]
    return None


def resolve_job_zone(
    neo4j_driver,
    company_name: str = "",
    location_display: str = "",
    location_area: str = "",
    description: str = "",
) -> Tuple[Optional[str], Optional[str]]:
    """
    Resolve MIDC zone and industry for a job using Neo4j.

    Resolution order:
      1. Exact company name lookup in KG → zone + industry
      2. Partial company name (CONTAINS) in KG
      3. Location text alias matching (zone_aliases)
      4. Description text alias matching
      5. Return (None, None) — never fabricate

    Args:
        neo4j_driver: active Neo4j GraphDatabase.driver instance (or None)
        company_name: raw company name from Adzuna
        location_display: Adzuna location.display_name
        location_area: Adzuna location.area joined
        description: cleaned job description (for fallback text scan)

    Returns:
        (midc_zone, industry) — both may be None
    """
    # ── Step 1 & 2: Neo4j company lookup ─────────────────────────────────────
    if neo4j_driver and company_name and len(company_name.strip()) > 2:
        try:
            with neo4j_driver.session() as sess:
                # Exact match first
                result = sess.run(
                    """
                    MATCH (c:Company)-[:LOCATED_IN]->(z:MIDCZone)
                    OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
                    WHERE toLower(c.name) = toLower($name)
                    RETURN z.name AS zone, i.name AS industry
                    LIMIT 1
                    """,
                    name=company_name.strip()[:80],
                )
                row = result.single()
                if row and row["zone"]:
                    logger.info(
                        f"KG exact match: '{company_name}' → zone={row['zone']} industry={row['industry']}"
                    )
                    return row["zone"], row.get("industry")

                # Fuzzy CONTAINS match
                result = sess.run(
                    """
                    MATCH (c:Company)-[:LOCATED_IN]->(z:MIDCZone)
                    OPTIONAL MATCH (c)-[:BELONGS_TO]->(i:Industry)
                    WHERE toLower(c.name) CONTAINS toLower($name)
                    RETURN z.name AS zone, i.name AS industry
                    LIMIT 1
                    """,
                    name=company_name.strip()[:40],
                )
                row = result.single()
                if row and row["zone"]:
                    logger.info(
                        f"KG fuzzy match: '{company_name}' → zone={row['zone']} industry={row['industry']}"
                    )
                    return row["zone"], row.get("industry")

        except Exception as e:
            logger.warning(f"Neo4j query error: {e}")

    # ── Step 3: Location text alias matching ──────────────────────────────────
    combined_loc = f"{location_display} {location_area}"
    zone = detect_zone_from_text(combined_loc)
    if zone:
        logger.info(f"Location alias match: '{combined_loc.strip()}' → zone={zone}")
        return zone, None

    # ── Step 4: Description scan (last resort before giving up) ──────────────
    zone = detect_zone_from_text(description[:500] if description else "")
    if zone:
        logger.info(f"Description alias match → zone={zone}")
        return zone, None

    # ── Step 5: No zone found ─────────────────────────────────────────────────
    logger.debug(f"No zone resolved for company='{company_name}' loc='{combined_loc.strip()}'")
    return None, None


def get_jobs_in_zone(neo4j_driver, zone_name: str) -> list[str]:
    """
    Return a list of source_job_ids for all jobs tagged to a given MIDC zone.
    Used during KG-first query retrieval.

    NOTE: This queries the AdzunaJob DB table, not the KG directly.
    The KG is used here only to validate that the zone name exists.
    Actual job filtering uses the AdzunaJob.midc_zone column.

    Returns list of source_job_ids (may be empty).
    """
    if not neo4j_driver:
        return []

    try:
        with neo4j_driver.session() as sess:
            result = sess.run(
                """
                MATCH (z:MIDCZone)
                WHERE toLower(z.name) = toLower($zone)
                RETURN z.name AS canonical
                LIMIT 1
                """,
                zone=zone_name,
            )
            row = result.single()
            if row:
                return row["canonical"]
    except Exception as e:
        logger.warning(f"KG zone validation error: {e}")

    return []
