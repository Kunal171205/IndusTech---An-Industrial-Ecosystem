"""
indusconnect/models_ic.py
==========================
SQLAlchemy model for Adzuna-sourced job listings.

This is ADDITIVE — it extends models.py without modifying existing tables.

AdzunaJob stores normalized, cleaned, zone-tagged, and embedded job data.
The embedding is stored as a binary blob for persistence; FAISS index
is rebuilt from these embeddings at startup / after ingestion.
"""

from database import db
from datetime import datetime
import json


class AdzunaJob(db.Model):
    """
    Canonical job listing obtained from the Adzuna API.

    source_job_id is the Adzuna job ID — used for deduplication.
    midc_zone is assigned by kg_resolver using Neo4j.
    embedding is a binary-serialised float32 numpy array (384 dims).
    """
    __tablename__ = "adzuna_job"

    id               = db.Column(db.Integer, primary_key=True)

    # ── Source information ─────────────────────────────────────────────────
    source           = db.Column(db.String(32),  nullable=False, default="adzuna")
    source_job_id    = db.Column(db.String(64),  nullable=False, unique=True, index=True)

    # ── Job details ────────────────────────────────────────────────────────
    title            = db.Column(db.String(255),  nullable=False)
    description      = db.Column(db.Text,         nullable=True)   # cleaned
    company_name     = db.Column(db.String(200),  nullable=True)

    # ── Location ───────────────────────────────────────────────────────────
    location_display = db.Column(db.String(200),  nullable=True)
    location_area    = db.Column(db.String(200),  nullable=True)
    latitude         = db.Column(db.Float,         nullable=True)
    longitude        = db.Column(db.Float,         nullable=True)
    midc_zone        = db.Column(db.String(80),    nullable=True, index=True)  # KG-assigned
    industry         = db.Column(db.String(120),   nullable=True)

    # ── Category / contract ────────────────────────────────────────────────
    category_label   = db.Column(db.String(120),  nullable=True)
    category_tag     = db.Column(db.String(80),   nullable=True)
    contract_type    = db.Column(db.String(80),   nullable=True)
    contract_time    = db.Column(db.String(80),   nullable=True)

    # ── Salary ────────────────────────────────────────────────────────────
    salary_min       = db.Column(db.Float,        nullable=True)
    salary_max       = db.Column(db.Float,        nullable=True)
    salary_is_predicted = db.Column(db.Boolean,   nullable=True)

    # ── Timestamps & status ────────────────────────────────────────────────
    created_at       = db.Column(db.DateTime,     nullable=True)   # from Adzuna
    ingested_at      = db.Column(db.DateTime,     nullable=False, default=datetime.utcnow)
    last_seen_at     = db.Column(db.DateTime,     nullable=True)
    active           = db.Column(db.Boolean,      nullable=False, default=True, index=True)

    # ── URLs ──────────────────────────────────────────────────────────────
    redirect_url     = db.Column(db.String(1024), nullable=True)

    # ── Embedding (binary blob, float32, 384-dim) ──────────────────────────
    embedding        = db.Column(db.LargeBinary,  nullable=True)

    # ── Raw source (JSON string) — kept for auditing ───────────────────────
    raw_data         = db.Column(db.Text,         nullable=True)

    def set_embedding(self, vec):
        """Store a numpy float32 array as bytes."""
        import numpy as np
        if vec is not None:
            self.embedding = np.array(vec, dtype=np.float32).flatten().tobytes()

    def get_embedding(self):
        """Load embedding back as a numpy float32 array of shape (384,)."""
        import numpy as np
        if self.embedding is None:
            return None
        return np.frombuffer(self.embedding, dtype=np.float32)

    def set_raw(self, data: dict):
        self.raw_data = json.dumps(data, default=str)

    def to_dict(self) -> dict:
        """Serialise to JSON-safe dict for API responses."""
        return {
            "id":               self.id,
            "source":           self.source,
            "source_job_id":    self.source_job_id,
            "title":            self.title,
            "description":      self.description,
            "company_name":     self.company_name,
            "location_display": self.location_display,
            "midc_zone":        self.midc_zone,
            "industry":         self.industry,
            "category_label":   self.category_label,
            "contract_type":    self.contract_type,
            "contract_time":    self.contract_time,
            "salary_min":       self.salary_min,
            "salary_max":       self.salary_max,
            "created_at":       self.created_at.isoformat() if self.created_at else None,
            "redirect_url":     self.redirect_url,
            "active":           self.active,
            "latitude":         self.latitude,
            "longitude":        self.longitude,
        }
