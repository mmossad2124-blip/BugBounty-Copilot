#!/usr/bin/env python3
"""
24/7 Daily Autonomous Scheduler Daemon
Schedules and triggers the full autonomous training relay every single day at 02:00 AM UTC.
Ensures zero-touch operation: wakes up, harvests novel 0-days, accumulates weights, and runs the sandbox.
"""

import os
import sys
import time
import subprocess
from datetime import datetime, timezone, timedelta

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RELAY_SCRIPT = os.path.join(REPO_DIR, "automation", "autonomous_relay_daemon.py")
SCHEDULE_LOG = os.path.join(REPO_DIR, "automation", "scheduler.log")

TARGET_HOUR_UTC = 2  # 02:00 AM UTC (approx 04:00 AM / 05:00 AM Cairo local time)
TARGET_MINUTE_UTC = 0

def log(msg):
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    line = f"[{timestamp}] {msg}"
    print(line, flush=True)
    with open(SCHEDULE_LOG, "a") as f:
        f.write(line + "\n")

def get_seconds_until_next_run():
    now = datetime.now(timezone.utc)
    target = now.replace(hour=TARGET_HOUR_UTC, minute=TARGET_MINUTE_UTC, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    diff = (target - now).total_seconds()
    return diff, target

def run_scheduler_loop():
    log("=" * 70)
    log("⏰ [24/7 MASTER SCHEDULER DAEMON] Initialized.")
    log(f"   Daily Scheduled Execution Time: {TARGET_HOUR_UTC:02d}:{TARGET_MINUTE_UTC:02d} UTC Every Day")
    log("=" * 70)

    while True:
        seconds_to_wait, target_time = get_seconds_until_next_run()
        hours = int(seconds_to_wait // 3600)
        minutes = int((seconds_to_wait % 3600) // 60)
        log(f"[*] Next Autonomous Relay Scheduled For: {target_time.strftime('%Y-%m-%d %H:%M:%S UTC')} (in {hours}h {minutes}m)")
        
        # Sleep until scheduled time
        time.sleep(seconds_to_wait)

        log("🚀 [SCHEDULE TRIGGERED] Waking up autonomous relay conductor for daily training cycle...")
        try:
            res = subprocess.run([sys.executable, RELAY_SCRIPT], check=True)
            log("[✓] Daily Autonomous Relay Cycle completed successfully!")
        except Exception as e:
            log(f"[!] Warning: Relay execution encountered exception: {e}")

        # Wait a short grace period before calculating next day
        time.sleep(60)

if __name__ == "__main__":
    run_scheduler_loop()
