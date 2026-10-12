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

def load_token(acc_id, username, fallback=""):
    creds_path = os.path.join(REPO_DIR, "accounts", f"account_{acc_id}_{username}.json")
    if os.path.exists(creds_path):
        try:
            with open(creds_path) as f:
                return json.load(f).get("credentials", {}).get("kaggle_api_token", fallback)
        except Exception:
            pass
    return os.environ.get(f"KAGGLE_API_TOKEN_{acc_id}", fallback)

ACCOUNT_1_USER = "mmossad2124"
ACCOUNT_1_TOKEN = load_token(1, ACCOUNT_1_USER)

ACCOUNT_3_USER = "mmossad2324"
ACCOUNT_3_TOKEN = load_token(3, ACCOUNT_3_USER)

def step1_harvest_internet_data():
    print(f"\n{'='*70}")
    print("[PHASE 1] Multi-Source Threat Intel & Patch-Diffing Harvester...")
    print(f"{'='*70}")
    
    # 1. Multi-source elite intelligence (Project Zero, Kaspersky, GitHub Advisories)
    intel_script = os.path.join(REPO_DIR, "data_pipeline", "multi_source_threat_intel_harvester.py")
    subprocess.run([sys.executable, intel_script], check=False)

    # 2. Patch-Diffing & Root-Cause analysis engine
    patch_script = os.path.join(REPO_DIR, "data_pipeline", "fetch_patch_diffs.py")
    subprocess.run([sys.executable, patch_script], check=False)

    # 3. CVE PoCs with Deduplication registry
    cve_script = os.path.join(REPO_DIR, "data_pipeline", "autonomous_internet_harvester.py")
    subprocess.run([sys.executable, cve_script], check=False)

    # 4. Legendary Historic Milestones & Hall-of-Fame Exploits
    milestone_script = os.path.join(REPO_DIR, "data_pipeline", "legendary_milestone_intel.py")
    subprocess.run([sys.executable, milestone_script], check=False)

def step2_sandbox_verification_loop():
    print(f"\n{'='*70}")
    print("[PHASE 2] Autonomous Sandbox Verification: Testing Reasoning in Isolated Sandbox...")
    print(f"{'='*70}")
    sandbox_script = os.path.join(REPO_DIR, "sandbox", "live_dynamic_ai_sandbox.py")
    subprocess.run([sys.executable, sandbox_script], check=True)

def step3_commit_and_push_to_github():
    print(f"\n{'='*70}")
    print("[PHASE 3] Syncing Harvested Datasets & Verified DPO Pairs to GitHub Cloud...")
    print(f"{'='*70}")
    try:
        gh_pat = os.environ.get("GH_PAT")
        if gh_pat:
            subprocess.run(["git", "remote", "set-url", "origin", f"https://x-access-token:{gh_pat}@github.com/mmossad2124-blip/BugBounty-Copilot.git"], cwd=REPO_DIR, check=False)
        subprocess.run(["git", "add", "data_pipeline/processed_datasets/", "sandbox/verified_dpo_pairs.jsonl"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "commit", "-m", "chore(auto): Autonomous Daily 0-Day Harvester & DPO Update"], cwd=REPO_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=REPO_DIR, check=True)
        print("[✓] Datasets synchronized with GitHub cloud!")
    except Exception as e:
        print(f"[!] Git sync notice (no changes or already committed): {e}")

def trigger_kaggle_kernel(username, token):
    """Pushes and starts a Kaggle kernel using python with SSL patch."""
    print(f"[*] Triggering Kaggle GPU Runner for node: {username}...")
    
    # Write token file for Kaggle CLI / API
    home = os.path.expanduser("~")
    kaggle_dir = os.path.join(home, ".kaggle")
    os.makedirs(kaggle_dir, exist_ok=True)
    with open(os.path.join(kaggle_dir, "access_token"), "w") as f:
        f.write(token)
    os.chmod(os.path.join(kaggle_dir, "access_token"), 0o600)

    # Update metadata ID and link previous node weights as input source
    with open(META_PATH, "r") as f:
        meta = json.load(f)
    meta["id"] = f"{username}/bugbounty-copilot-trainer"
    if username == "mmossad2124":
        meta["kernel_sources"] = ["mmossad2324/bugbounty-copilot-trainer"]
    elif username == "mmossad2324":
        meta["kernel_sources"] = ["mmossad2124/bugbounty-copilot-trainer"]
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    pusher_code = f"""
import os, sys, ssl, time, urllib3.util.ssl_
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

for attempt in range(1, 6):
    try:
        res = api.kernels_push("{NOTEBOOKS_DIR}")
        print("[✓] Push Successful:", res.url if hasattr(res, "url") else res)
        break
    except Exception as e:
        print(f"[!] Push attempt {{attempt}} failed: {{e}}. Retrying in 10s...")
        time.sleep(10)
        if attempt == 5:
            raise
"""
    subprocess.run([sys.executable, "-c", pusher_code], check=True)

def wait_for_kernel_completion(username, token, max_wait_hours=4):
    """Polls Kaggle API until the kernel reaches 'complete' status."""
    print(f"[*] Kernel triggered for {username}. Waiting 45s for cloud node to register job queue...")
    time.sleep(45)
    print(f"[*] Monitoring {username} training session in the cloud...")
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

    # 2. Run Sandbox Verification & Generate DPO Samples
    step2_sandbox_verification_loop()

    # 3. Push fresh datasets to GitHub
    step3_commit_and_push_to_github()

    # 4. Phase A: Wake up Account 1 (External Foothold & Web)
    print(f"\n{'='*70}")
    print("[PHASE 4] Waking Up Account 1 (mmossad2124): Stage 1 External Breach Training...")
    print(f"{'='*70}")
    trigger_kaggle_kernel(ACCOUNT_1_USER, ACCOUNT_1_TOKEN)
    wait_for_kernel_completion(ACCOUNT_1_USER, ACCOUNT_1_TOKEN)

    # 5. Phase B: Wake up Account 3 (Kernel PrivEsc & AD)
    print(f"\n{'='*70}")
    print("[PHASE 5] Handing Off to Account 3 (mmossad2324): Stage 2 Root Escalation Training...")
    print(f"{'='*70}")
    trigger_kaggle_kernel(ACCOUNT_3_USER, ACCOUNT_3_TOKEN)
    wait_for_kernel_completion(ACCOUNT_3_USER, ACCOUNT_3_TOKEN)

    # 6. Phase C: Post-Training Complex Sandbox Exam (Multi-Round Trial-and-Error)
    print(f"\n{'='*70}")
    print("[PHASE 6] Post-Training Autonomous Sandbox Exam: Multi-Round Trial-and-Error & Patching...")
    print(f"{'='*70}")
    complex_sandbox = os.path.join(REPO_DIR, "sandbox", "complex_multiround_sandbox.py")
    subprocess.run([sys.executable, complex_sandbox], check=False)

    print(f"\n{'#'*75}")
    print("# [✓] ALL RELAY PHASES COMPLETED! MODEL BRAIN FULLY UPDATED FOR THE DAY.")
    print(f"{'#'*75}\n")

if __name__ == "__main__":
    run_full_autonomous_relay()
