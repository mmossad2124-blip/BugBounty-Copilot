#!/usr/bin/env python3
"""
Multi-Account Kaggle Cluster Orchestrator (90 Hours / Week)
Rotates across Account 1, Account 2, and Account 3 to balance GPU quotas
and execute specialized training stages (SFT, DPO, ALAS Self-Evolution).
"""

import os
import subprocess
import json

ACCOUNTS = [
    {
        "id": 1,
        "username": "mmossad2124",
        "token": "KGAT_8674338cd01a502688c872dcfb449c9c",
        "stage": "STAGE_1_DEEP_SFT",
        "role": "Deep Knowledge Acquisition & Multi-Vector Exploitation"
    },
    {
        "id": 2,
        "username": "mmossad2224",
        "token": "KGAT_4742ca67eb0db8c50680e2b722869334",
        "stage": "STAGE_2_DPO_ALIGNMENT",
        "role": "Deep Thinking & Exploit Chaining Contrastive Optimization"
    },
    {
        "id": 3,
        "username": "mmossad2324",
        "token": "KGAT_48bbd3cfad1e206ad99d7b5eb66f22e8",
        "stage": "STAGE_3_ALAS_SELF_EVOLUTION",
        "role": "Autonomous Synthetic Data Generation & Gap-Patching Loop"
    }
]

def run_stage(account):
    print(f"\n{'='*60}")
    print(f"[*] Activating Kaggle Cluster Node: {account['username']} (Account {account['id']})")
    print(f"[*] Assigned Stage: {account['stage']}")
    print(f"[*] Role: {account['role']}")
    print(f"{'='*60}")

    env = os.environ.copy()
    env["KAGGLE_API_TOKEN"] = account["token"]

    # Write access token
    home = os.path.expanduser("~")
    kaggle_dir = os.path.join(home, ".kaggle")
    os.makedirs(kaggle_dir, exist_ok=True)
    with open(os.path.join(kaggle_dir, "access_token"), "w") as f:
        f.write(account["token"])
    os.chmod(os.path.join(kaggle_dir, "access_token"), 0o600)

    # Update kernel-metadata.json
    notebooks_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "notebooks")
    metadata_path = os.path.join(notebooks_dir, "kernel-metadata.json")
    
    with open(metadata_path, "r") as f:
        meta = json.load(f)
    
    meta["id"] = f"{account['username']}/bugbounty-copilot-trainer"
    with open(metadata_path, "w") as f:
        json.dump(meta, f, indent=2)

    # Push and start training
    cmd = ["kaggle", "kernels", "push", "-p", notebooks_dir]
    try:
        res = subprocess.run(cmd, env=env, capture_output=True, text=True, check=True)
        print(f"[✓] Successfully triggered: {res.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        print(f"[!] Warning: {e.stderr.strip() if e.stderr else e}")

if __name__ == "__main__":
    import sys
    # Usage: python account_rotator.py [1|2|3] or all
    choice = sys.argv[1] if len(sys.argv) > 1 else "1"
    if choice == "all":
        for acc in ACCOUNTS:
            run_stage(acc)
    else:
        idx = int(choice) - 1
        run_stage(ACCOUNTS[idx])
