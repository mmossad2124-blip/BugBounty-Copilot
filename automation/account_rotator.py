#!/usr/bin/env python3
"""
Multi-Account Kaggle Cluster Orchestrator (Dual-Node: Account 1 & Account 3)
Permanently configured to route between Account 1 (mmossad2124) and Account 3 (mmossad2324)
handling SFT, DPO Alignment, and Autonomous Self-Evolution.
"""

import os
import subprocess
import json

def load_account_config(acc_id, username, fallback_token, stage, role):
    creds_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "accounts", f"account_{acc_id}_{username}.json")
    token = fallback_token
    if os.path.exists(creds_path):
        try:
            with open(creds_path) as f:
                data = json.load(f)
                token = data.get("credentials", {}).get("kaggle_api_token", fallback_token)
        except Exception:
            pass
    return {
        "id": acc_id,
        "username": username,
        "token": token,
        "stage": stage,
        "role": role
    }

ACCOUNTS = [
    load_account_config(1, "mmossad2124", os.environ.get("KAGGLE_TOKEN_1", ""), "STAGE_1_WEB_CLOUD_DPO", "Initial Foothold, Web/API Exploitation & DPO Reasoning Track 1"),
    load_account_config(3, "mmossad2324", os.environ.get("KAGGLE_TOKEN_3", ""), "STAGE_2_PRIVESC_KERNEL_DPO", "Kernel PrivEsc, Active Directory Dominance & DPO Reasoning Track 2")
]

def run_stage(account):
    print(f"\n{'='*65}")
    print(f"[*] Activating Dedicated Cluster Node: {account['username']} (Account {account['id']})")
    print(f"[*] Assigned Stage: {account['stage']}")
    print(f"[*] Specialization: {account['role']}")
    print(f"{'='*65}")

    env = os.environ.copy()
    env["KAGGLE_API_TOKEN"] = account["token"]

    # Write access token
    home = os.path.expanduser("~")
    kaggle_dir = os.path.join(home, ".kaggle")
    os.makedirs(kaggle_dir, exist_ok=True)
    with open(os.path.join(kaggle_dir, "access_token"), "w") as f:
        f.write(account["token"])
    os.chmod(os.path.join(kaggle_dir, "access_token"), 0o600)

    notebooks_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notebooks")
    metadata_path = os.path.join(notebooks_dir, "kernel-metadata.json")
    
    with open(metadata_path, "r") as f:
        meta = json.load(f)
    
    meta["id"] = f"{account['username']}/bugbounty-copilot-trainer"
    with open(metadata_path, "w") as f:
        json.dump(meta, f, indent=2)

    pusher_code = f"""
import os, sys, ssl, urllib3.util.ssl_
orig = urllib3.util.ssl_.create_urllib3_context
def patched(*args, **kwargs):
    ctx = orig(*args, **kwargs)
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    return ctx
urllib3.util.ssl_.create_urllib3_context = patched
os.environ["KAGGLE_API_TOKEN"] = "{account['token']}"
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
res = api.kernels_push("{notebooks_dir}")
print("[✓] Kaggle Node Triggered Successfully:", res.url if hasattr(res, "url") else res)
"""
    subprocess.run([sys.executable, "-c", pusher_code], check=True)

if __name__ == "__main__":
    import sys
    choice = sys.argv[1] if len(sys.argv) > 1 else "1"
    if choice == "all":
        for acc in ACCOUNTS:
            run_stage(acc)
    elif choice in ["1", "3"]:
        target = [a for a in ACCOUNTS if a["id"] == int(choice)][0]
        run_stage(target)
    else:
        print("[!] Invalid account ID. Use '1', '3', or 'all'.")
