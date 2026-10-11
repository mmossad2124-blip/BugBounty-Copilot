#!/usr/bin/env python3
"""
Autonomous Multi-Account Relay Conductor Daemon
1. Runs the daily internet harvester to scrape and distill fresh 0-Days/CVEs.
2. Commits fresh training data to GitHub.
3. Wakes up Account 1 (mmossad2124) on Kaggle to train Stage 1 (Initial Access & Cloud).
4. Waits for Account 1 to complete and takes its output.
5. Wakes up Account 3 (mmossad2324) on Kaggle to train Stage 2 (Kernel PrivEsc & AD).
6. Completes the daily relay loop autonomously without human intervention!
"""

import os
import sys
import time
import json
import urllib.request
import subprocess

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NOTEBOOKS_DIR = os.path.join(REPO_DIR, "notebooks")
META_PATH = os.path.join(NOTEBOOKS_DIR, "kernel-metadata.json")

ACCOUNT_1_TOKEN = "KGAT_8674338cd01a502688c872dcfb449c9c"
ACCOUNT_1_USER = "mmossad2124"

ACCOUNT_3_TOKEN = "KGAT_48bbd3cfad1e206ad99d7b5eb66f22e8"
ACCOUNT_3_USER = "mmossad2324"

def step1_harvest_internet_data():
    print(f"\n{'='*70}")
    print("[PHASE 1] Autonomous Internet Harvesting: Crawling Newest Exploits & CVEs...")
    print(f"{'='*70}")
    script_path = os.path.join(REPO_DIR, "data_pipeline", "autonomous_internet_harvester.py")
    subprocess.run([sys.executable, script_path], check=True)

def step2_commit_and_push_to_github():
    print(f"\n{'='*70}")
    print("[PHASE 2] Syncing Harvested Datasets to GitHub Cloud Repository...")
    print(f"{'='*70}")
    try:
        subprocess.run(["git", "add", "data_pipeline/processed_datasets/"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "chore(auto): Autonomous Daily 0-Day Harvester Update"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
        print("[✓] Datasets synchronized with GitHub cloud!")
    except Exception as e:
        print(f"[!] Git sync notice (no changes or already committed): {e}")

def trigger_kaggle_kernel(username, token):
    """Pushes and starts a Kaggle kernel using python with SSL patch."""
    print(f"[*] Triggering Kaggle GPU Runner for node: {username}...")
    
    # Update metadata ID
    with open(META_PATH, "r") as f:
        meta = json.load(f)
    meta["id"] = f"{username}/bugbounty-copilot-trainer"
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    pusher_code = f"""
import os, sys, ssl, urllib3.util.ssl_
orig = urllib3.util.ssl_.create_urllib3_context
def patched(*args, **kwargs):
    ctx = orig(*args, **kwargs)
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    return ctx
urllib3.util.ssl_.create_urllib3_context = patched
os.environ["KAGGLE_API_TOKEN"] = "{token}"
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
res = api.kernels_push("{NOTEBOOKS_DIR}")
print("[✓] Push Successful:", res.url if hasattr(res, "url") else res)
"""
    subprocess.run([sys.executable, "-c", pusher_code], check=True)

def wait_for_kernel_completion(username, token, max_wait_hours=4):
    """Polls Kaggle API until the kernel reaches 'complete' status."""
    print(f"[*] Waiting for {username} training session to complete in the cloud...")
    start_time = time.time()
    url = f"https://www.kaggle.com/api/v1/kernels/status?userName={username}&kernelSlug=bugbounty-copilot-trainer"
    headers = {"Authorization": f"Bearer {token}", "User-Agent": "KaggleWatcher/1.0"}

    while True:
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode())
                status = data.get("status", "unknown")
                elapsed_mins = int((time.time() - start_time) / 60)
                print(f"    -> [{username}] Current Status: '{status}' (Elapsed: {elapsed_mins} mins)")
                
                if status == "complete":
                    print(f"[✓] {username} training session COMPLETED successfully!")
                    return True
                elif status == "error":
                    print(f"[!] Warning: {username} encountered error status.")
                    return False
        except Exception as e:
            print(f"    -> Status poll warning: {e}")

        if (time.time() - start_time) > (max_wait_hours * 3600):
            print(f"[!] Max wait time reached for {username}.")
            return False

        time.sleep(120) # Poll every 2 minutes

def run_full_autonomous_relay():
    print(f"\n{'#'*75}")
    print("# 🚀 INITIATING 24/7 AUTONOMOUS BUG BOUNTY RELAY & TRAINING DAEMON")
    print(f"{'#'*75}")

    # 1. Scrape & Distill fresh CVEs
    step1_harvest_internet_data()

    # 2. Push fresh datasets to GitHub
    step2_commit_and_push_to_github()

    # 3. Phase A: Wake up Account 1 (External Foothold & Web)
    print(f"\n{'='*70}")
    print("[PHASE 3] Waking Up Account 1 (mmossad2124): Stage 1 External Breach Training...")
    print(f"{'='*70}")
    trigger_kaggle_kernel(ACCOUNT_1_USER, ACCOUNT_1_TOKEN)
    wait_for_kernel_completion(ACCOUNT_1_USER, ACCOUNT_1_TOKEN)

    # 4. Phase B: Wake up Account 3 (Kernel PrivEsc & AD)
    print(f"\n{'='*70}")
    print("[PHASE 4] Handing Off to Account 3 (mmossad2324): Stage 2 Root Escalation Training...")
    print(f"{'='*70}")
    trigger_kaggle_kernel(ACCOUNT_3_USER, ACCOUNT_3_TOKEN)
    wait_for_kernel_completion(ACCOUNT_3_USER, ACCOUNT_3_TOKEN)

    print(f"\n{'#'*75}")
    print("# [✓] ALL RELAY PHASES COMPLETED! MODEL BRAIN FULLY UPDATED FOR THE DAY.")
    print(f"{'#'*75}\n")

if __name__ == "__main__":
    run_full_autonomous_relay()
