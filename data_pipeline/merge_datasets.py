#!/usr/bin/env python3
"""
Master Dataset Merging Engine
Combines Web Exploitation (PentesterLand), Privilege Escalation (PrivEsc Arsenal),
and Active Directory Tradecraft into a single master training dataset.
"""

import os
import glob

DATASETS_DIR = os.path.join(os.path.dirname(__file__), "processed_datasets")
MASTER_OUTPUT = os.path.join(DATASETS_DIR, "master_redteam_cot.jsonl")

def merge_all():
    files = glob.glob(os.path.join(DATASETS_DIR, "*.jsonl"))
    total_lines = 0
    
    with open(MASTER_OUTPUT, "w", encoding="utf-8") as out_f:
        for f in files:
            if os.path.abspath(f) == os.path.abspath(MASTER_OUTPUT):
                continue
            with open(f, "r", encoding="utf-8") as in_f:
                for line in in_f:
                    if line.strip():
                        out_f.write(line.strip() + "\n")
                        total_lines += 1

    print(f"[✓] Successfully merged {total_lines} total samples into {MASTER_OUTPUT}")

if __name__ == "__main__":
    merge_all()
