"""
indusconnect/cleaning.py
========================
Job description cleaning for IndusConnect.

Removes boilerplate, HTML, duplicated whitespace while preserving
skills, experience requirements, responsibilities, location, and
company information needed for semantic embeddings.
"""

import re
import html
import logging

logger = logging.getLogger("[CLEANING]")

# ── Boilerplate patterns to strip ────────────────────────────────────────────
_BOILERPLATE_PATTERNS = [
    # Contact / apply CTAs
    r"(send (your )?(cv|resume|application)|apply (now|online|here|today))[^\n]*",
    r"(contact us|reach us|call us|email us|whatsapp)[^\n]*",
    r"\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b",  # email addresses
    r"\+?\d[\d\s\-().]{7,}\d",           # phone numbers
    r"https?://\S+",                      # URLs
    # Repeated disclaimer/EEO
    r"(equal opportunity|we are an equal|eeo|affirmative action)[^\n]*",
    r"(note:|disclaimer:|important:)[^\n]*",
    # Generic filler
    r"(click here|submit your|upload your)[^\n]*",
    r"(salary (is )?(negotiable|commensurate))[^\n]*",
    r"(urgent (requirement|hiring|opening))[^\n]*",
    r"(walk.in|walk in) interview[^\n]*",
    r"(freshers?|experienced|0.?\s*-?\s*\d+ years?)[^\n]*welcome[^\n]*",
    # Naukri / Indeed footer artefacts
    r"(role category|functional area|industry|role)[:\s]*\n",
    r"key skills\s*$",
    r"^\s*\*+\s*$",  # lines of asterisks
]

_BOILERPLATE_RE = re.compile(
    "|".join(_BOILERPLATE_PATTERNS),
    flags=re.IGNORECASE | re.MULTILINE,
)


def _strip_html(text: str) -> str:
    """Remove HTML tags and unescape HTML entities."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    return text


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple spaces/newlines, strip leading/trailing whitespace."""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _remove_boilerplate(text: str) -> str:
    """Strip contact info, apply CTAs, and generic filler."""
    return _BOILERPLATE_RE.sub(" ", text)


def clean_job_description(description: str) -> str:
    """
    Full cleaning pipeline for a raw job description.

    Steps:
      1. Strip HTML tags and unescape entities
      2. Remove boilerplate (contact info, CTA phrases, URLs, emails)
      3. Normalize whitespace

    Preserves:
      - Job title context (caller should pass title separately)
      - Skills and experience requirements
      - Responsibilities
      - Location mentions
      - Company context

    Returns cleaned text suitable for semantic embedding.
    """
    if not description:
        return ""

    text = _strip_html(description)
    text = _remove_boilerplate(text)
    text = _normalize_whitespace(text)

    logger.debug(f"Cleaned description: {len(description)} → {len(text)} chars")
    return text


def build_embedding_text(job: dict) -> str:
    """
    Construct the text string that will be embedded for a job.

    Uses: title, company, cleaned description, industry, location, contract type.
    Does NOT embed raw metadata like salary, source IDs, or redirect URLs.

    Args:
        job: dict with keys title, company_name, description, industry,
             location_display, contract_time (all optional, handled defensively)

    Returns:
        Formatted embedding text string.
    """
    parts = []

    if job.get("title"):
        parts.append(f"Title: {job['title']}")

    if job.get("company_name"):
        parts.append(f"Company: {job['company_name']}")

    if job.get("description"):
        # Use first 500 chars of cleaned description for embedding
        desc = job["description"][:500].strip()
        if desc:
            parts.append(f"Description: {desc}")

    if job.get("industry"):
        parts.append(f"Industry: {job['industry']}")

    if job.get("midc_zone"):
        parts.append(f"Location: {job['midc_zone']} MIDC")
    elif job.get("location_display"):
        parts.append(f"Location: {job['location_display']}")

    if job.get("contract_time"):
        parts.append(f"Contract: {job['contract_time']}")

    return "\n".join(parts)
