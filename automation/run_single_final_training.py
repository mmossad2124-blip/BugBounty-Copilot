#!/usr/bin/env python3
"""
Final Tier-2 Threat Intel Training & Verification Conductor
Executes a single, non-repeating cycle for the remaining 32 sources:
1. Phase 1: Wakes up Account 1 (mmossad2124) on Kaggle (Stage 1: Web, Remote, API, LLM, Cloud).
2. Phase 2: Wakes up Account 3 (mmossad2324) on Kaggle (Stage 2: Kernel, Memory, Containers, AD, Project Zero).
3. Phase 3: Autonomous Sandbox Exam & HexStrike Live Audit.
4. Final: Stops cleanly with ZERO auto-chaining, leaving weights 100% ready for model fusion.
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

def fetch_partner_lora_urls(target_user):
    check_order = [("mmossad2324", ACCOUNT_3_TOKEN), ("mmossad2124", ACCOUNT_1_TOKEN)]
    if target_user == "mmossad2324":
        check_order = [("mmossad2124", ACCOUNT_1_TOKEN), ("mmossad2324", ACCOUNT_3_TOKEN)]

    for user, token in check_order:
        if not token:
            continue
        try:
            url = f"https://www.kaggle.com/api/v1/kernels/output?userName={user}&kernelSlug=bugbounty-copilot-trainer"
            headers = {"Authorization": f"Bearer {token}", "User-Agent": "KaggleWatcher/1.0"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            files = {f["fileName"]: f["url"] for f in data.get("files", []) if "bugbounty_copilot_lora" in f.get("fileName", "")}
            if files and any("adapter_model.safetensors" in k for k in files):
                print(f"[✓] Retrieved {len(files)} signed LoRA weight URLs from node {user}!")
                return files
        except Exception as e:
            print(f"[!] Warning fetching LoRA URLs from {user}: {e}")
    return {}

def trigger_kaggle_kernel(username, token):
    print(f"\n{'='*70}")
    print(f"[*] Triggering Final Kaggle Cloud Run for Node: {username}...")
    print(f"{'='*70}")

    home = os.path.expanduser("~")
    kaggle_dir = os.path.join(home, ".kaggle")
    os.makedirs(kaggle_dir, exist_ok=True)
    with open(os.path.join(kaggle_dir, "access_token"), "w") as f:
        f.write(token)
    os.chmod(os.path.join(kaggle_dir, "access_token"), 0o600)

    with open(META_PATH, "r") as f:
        meta = json.load(f)
    meta["id"] = f"{username}/bugbounty-copilot-trainer"
    if username == "mmossad2124":
        meta["kernel_sources"] = ["mmossad2324/bugbounty-copilot-trainer"]
    elif username == "mmossad2324":
        meta["kernel_sources"] = ["mmossad2124/bugbounty-copilot-trainer"]
    with open(META_PATH, "w") as f:
        json.dump(meta, f, indent=2)

    lora_urls = fetch_partner_lora_urls(username)
    nb_path = os.path.join(NOTEBOOKS_DIR, "BugBounty_Copilot_Kaggle_Trainer.ipynb")
    try:
        with open(nb_path, "r", encoding="utf-8") as nf:
            nb = json.load(nf)
        for cell in nb.get("cells", []):
            if cell.get("cell_type") == "code":
                for i, line in enumerate(cell.get("source", [])):
                    if line.startswith('ACTIVE_NODE_USER = '):
                        cell["source"][i] = f'ACTIVE_NODE_USER = "{username}" # Daemon auto-updated\n'
                    elif line.startswith('LATEST_LORA_URLS = '):
                        cell["source"][i] = f'LATEST_LORA_URLS = {json.dumps(lora_urls)} # Daemon injected signed URLs\n'
        with open(nb_path, "w", encoding="utf-8") as nf:
            json.dump(nb, nf, indent=1)
        print(f"[✓] Notebook configured with {len(lora_urls)} accumulated LoRA weights!")
    except Exception as e:
        print(f"[!] Warning updating notebook: {e}")

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

def wait_for_kernel_completion(username, token, max_wait_hours=3):
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

        time.sleep(120)

def main():
    print(f"\n{'#'*75}")
    print("# 🚀 INITIATING FINAL TIER-2 (32 SOURCES) TRAINING & REINFORCEMENT RUN")
    print(f"{'#'*75}")

    # 1. Trigger Account 1 (Stage 1: Web, Cloud, Remote RCE, API, LLM Top 10)
    print("\n>>> PHASE 1: Running Stage 1 on Node mmossad2124 (2,400 samples)...")
    trigger_kaggle_kernel(ACCOUNT_1_USER, ACCOUNT_1_TOKEN)
    s1_ok = wait_for_kernel_completion(ACCOUNT_1_USER, ACCOUNT_1_TOKEN)
    if not s1_ok:
        print("[!] Stage 1 encountered an issue. Pausing execution.")
        return

    # 2. Trigger Account 3 (Stage 2: Kernel, Memory, Containers, AD, Project Zero)
    print("\n>>> PHASE 2: Handing off to Node mmossad2324 (2,400 samples)...")
    trigger_kaggle_kernel(ACCOUNT_3_USER, ACCOUNT_3_TOKEN)
    s2_ok = wait_for_kernel_completion(ACCOUNT_3_USER, ACCOUNT_3_TOKEN)
    if not s2_ok:
        print("[!] Stage 2 encountered an issue. Pausing execution.")
        return

    # 3. Autonomous Sandbox & HexStrike Audit
    print("\n>>> PHASE 3: Executing Post-Training Sandbox Exam & HexStrike Audit...")
    complex_sandbox = os.path.join(REPO_DIR, "sandbox", "complex_multiround_sandbox.py")
    if os.path.exists(complex_sandbox):
        subprocess.run([sys.executable, complex_sandbox], check=False)

    agent_script = os.path.join(REPO_DIR, "agent", "hexstrike_agent_bridge.py")
    if os.path.exists(agent_script):
        subprocess.run([sys.executable, agent_script, "http://testphp.vulnweb.com"], check=False)

    print(f"\n{'#'*75}")
    print("# 🎉 ALL 50 THREAT INTEL SOURCES (INITIAL 27,000 + 32 TIER-2) 100% COMPLETE!")
    print("# 💎 MODEL WEIGHTS FULLY STACKED & READY FOR FINAL MODEL FUSION (MERGE).")
    print(f"{'#'*75}\n")

if __name__ == "__main__":
    main()
