"""
indusconnect/scheduler.py
=========================
APScheduler setup for daily job ingestion.
Replaces the old scheduler_setup.py.
"""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from indusconnect.ingestion import run_ingestion_pipeline

logger = logging.getLogger("[SCHEDULER]")

scheduler = BackgroundScheduler()
_scheduler_started = False

def run_daily_ingestion_job(app, neo4j_driver):
    """Wrapper that runs the ingestion pipeline within Flask app context."""
    logger.info("Starting daily Adzuna job ingestion...")
    try:
        with app.app_context():
            run_ingestion_pipeline(neo4j_driver=neo4j_driver)
    except Exception as e:
        logger.error(f"Scheduled ingestion failed: {e}")

def start_scheduler(app, neo4j_driver):
    """Call this once from app.py to start the background scheduler."""
    global _scheduler_started
    if _scheduler_started:
        return

    # Run every 24 hours
    scheduler.add_job(
        func=run_daily_ingestion_job,
        args=[app, neo4j_driver],
        trigger="interval",
        hours=24,
        id="indusconnect_daily_ingestion"
    )
    scheduler.start()
    _scheduler_started = True

    logger.info("IndusConnect daily ingestion scheduled (24h interval).")
