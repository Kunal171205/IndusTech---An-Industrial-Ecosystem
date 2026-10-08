"""
scheduler_setup.py
==================
Add this to your app.py to auto-run the scraper every 6 hours.

INSTALL:
    pip install apscheduler --break-system-packages

USAGE in app.py — paste these lines just before  if __name__ == "__main__":

    from scheduler_setup import start_scheduler
    start_scheduler()
"""

import os
import asyncio
import json
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()
_scheduler_started = False

def run_scraper_job():
    """Wrapper that runs the scraper synchronously for APScheduler."""
    print("[Scheduler] Starting Naukri/Jobhai scraper...")
    try:
        # Import here to avoid circular imports
        from scraper import scrape_and_store
        
        jobs = scrape_and_store()

        print(f"[Scheduler] Done — {len(jobs)} jobs cached.")
    except Exception as e:
        print(f"[Scheduler] Error: {e}")

def start_scheduler():
    """Call this once from app.py to start the background scheduler."""
    global _scheduler_started
    if _scheduler_started:
        return

    # Run once at startup, then every 6 hours
    scheduler.add_job(run_scraper_job, "interval", hours=6, id="midc_scraper")
    scheduler.start()
    _scheduler_started = True

    # Run immediately on first startup in background
    import threading
    t = threading.Thread(target=run_scraper_job, daemon=True)
    t.start()

    print("[Scheduler] MIDC job scraper scheduled every 6 hours.")