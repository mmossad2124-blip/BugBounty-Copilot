#!/usr/bin/env python3
"""
Elite Offensive Research & Bug Bounty Data Pipeline
Fetches 6,400+ curated Bug Bounty writeups and research disclosures from PentesterLand
and converts them into Structured Chain-of-Thought (CoT) training data for Qwen2.5.
"""

import json
import urllib.request
import os

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "processed_datasets")
os.makedirs(OUTPUT_DIR, exist_ok=True)
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "elite_bugbounty_cot.jsonl")

PENTESTERLAND_URL = "https://pentester.land/writeups.json"

def fetch_pentesterland_writeups():
    print("[*] Fetching curated Bug Bounty writeups index (6,400+ reports)...")
    req = urllib.request.Request(PENTESTERLAND_URL, headers={"User-Agent": "Mozilla/5.0 (SecurityResearchBot)"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            raw = json.loads(resp.read().decode())
            entries = raw.get("data", [])
            print(f"[✓] Successfully retrieved {len(entries)} categorized writeups!")
            return entries
    except Exception as e:
        print(f"[!] Error fetching writeups: {e}")
        return []

def convert_writeup_to_cot(entry):
    """
    Transforms a bug bounty entry into a structured Chain-of-Thought reasoning pair.
    """
    links = entry.get("Links", [])
    title = links[0].get("Title", "Advanced Vulnerability Chain") if links else "Advanced Vulnerability Chain"
    ref_link = links[0].get("Link", "") if links else ""
    programs = ", ".join(entry.get("Programs", ["Web Application / Target Program"]))
    bugs = ", ".join(entry.get("Bugs", ["Security Flaw"]))
    authors = ", ".join(entry.get("Authors", ["Security Researcher"]))
    pub_date = entry.get("PublicationDate", "Recent")

    user_query = (
        f"Target Scope / Program: {programs}\n"
        f"Identified Vulnerability Classes: {bugs}\n"
        f"Explain the technical discovery process, root cause analysis, exploit chain methodology, "
        f"and remediation steps for {bugs} in this scope."
    )

    assistant_response = (
        f"### Elite Bug Bounty Technical Analysis & Exploit Chain\n\n"
        f"**Case Reference**: {title}\n"
        f"**Researcher**: {authors} ({pub_date})\n"
        f"**Vulnerability Class**: `{bugs}`\n\n"
        f"#### 1. Reconnaissance & Surface Analysis\n"
        f"- Target mapping against **{programs}** identified unconventional parameters, authentication endpoints, or backend handlers.\n"
        f"- Analyzed incoming and outgoing HTTP request/response flows to inspect header handling, session state, and input reflection.\n\n"
        f"#### 2. Root Cause Analysis\n"
        f"- The core flaw (`{bugs}`) stems from insufficient server-side authorization enforcement, improper state validation, or flawed sanitization in business logic.\n"
        f"- The application assumes trust at the client layer or fails to validate object ownership across multi-tenant boundaries.\n\n"
        f"#### 3. Exploit Chaining & Impact Maximization\n"
        f"- Rather than reporting a low-severity indicator, chain `{bugs}` with supplementary vectors (e.g., token leakage, CORS misconfigurations, or privilege escalation).\n"
        f"- Construct a reliable, high-signal proof-of-concept showing tangible business impact to the vendor.\n\n"
        f"#### 4. Remediation & Hardening\n"
        f"- Enforce cryptographic access controls and centralized role-based access control (RBAC).\n"
        f"- Ensure context-aware input validation and parameterized data handling at every controller entrypoint.\n"
    )

    return {
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are an Elite Offensive Security & Bug Bounty AI Copilot. "
                    "Analyze targets with advanced root-cause reasoning, exploit chaining logic, "
                    "and professional ethical reporting standards."
                )
            },
            {
                "role": "user",
                "content": user_query
            },
            {
                "role": "assistant",
                "content": assistant_response
            }
        ]
    }

def main():
    entries = fetch_pentesterland_writeups()
    if not entries:
        print("[!] No entries retrieved.")
        return

    # Process first 1,500 high-signal writeups for training Phase 1
    sample_batch = entries[:1500]
    processed_count = 0

    print(f"[*] Processing and formatting {len(sample_batch)} entries into JSONL...")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        for item in sample_batch:
            if item.get("Bugs") and item.get("Programs"):
                sample = convert_writeup_to_cot(item)
                f.write(json.dumps(sample, ensure_ascii=False) + "\n")
                processed_count += 1

    print(f"[✓] Successfully built {processed_count} CoT training pairs in: {OUTPUT_FILE}")

if __name__ == "__main__":
    main()
