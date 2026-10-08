"""
run_ingestion.py
================
CLI entry point to manually trigger Adzuna job ingestion.
"""

import sys
import logging
from app import app, _neo4j_driver
from indusconnect.ingestion import run_ingestion_pipeline

logging.basicConfig(level=logging.INFO)

if __name__ == "__main__":
    print("Starting manual ingestion...")
    with app.app_context():
        stats = run_ingestion_pipeline(neo4j_driver=_neo4j_driver)
        if stats["status"] == "error":
            sys.exit(1)
        sys.exit(0)
