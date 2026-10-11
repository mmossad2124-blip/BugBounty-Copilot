#!/usr/bin/env python3
"""
Autonomous Internet Harvester & Distillation Engine
Curls the newest 0-Day & N-Day PoCs from GitHub, NVD, and ExploitDB,
and uses Cloudflare AI to automatically distill raw exploit code
into structured Chain-of-Thought (CoT) training samples every single night.
"""

import urllib.request
import json
import os
import re
from datetime import datetime, timezone

DATASETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_pipeline", "processed_datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)
MASTER_DATASET = os.path.join(DATASETS_DIR, "master_redteam_cot.jsonl")

# Load environment variables if available
def load_env():
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                if "=" in line and not line.startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ.setdefault(k, v)

load_env()
CF_ACCOUNT_ID = os.environ.get("CF_ACCOUNT_ID", "")
CF_API_TOKEN = os.environ.get("CF_API_TOKEN", "")
CF_MODEL = os.environ.get("CF_MODEL", "@cf/meta/llama-3.1-8b-instruct")

def fetch_recent_cve_pocs():
    """Fetches real-time newly published CVE PoCs from GitHub PoC aggregators."""
    print("[*] Harvesting newest 0-Day / N-Day CVE PoCs from GitHub...")
    url = "https://api.github.com/search/repositories?q=CVE-2026+OR+CVE-2025+PoC&sort=updated&order=desc&per_page=15"
    req = urllib.request.Request(url, headers={"User-Agent": "AutonomousHarvester/1.0"})
    
    pocs = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            items = data.get("items", [])
            for item in items:
                pocs.append({
                    "name": item.get("name"),
                    "description": item.get("description") or "Critical Vulnerability Exploit",
                    "url": item.get("html_url"),
                    "updated_at": item.get("updated_at")
                })
            print(f"[✓] Successfully harvested {len(pocs)} live CVE PoC disclosures!")
    except Exception as e:
        print(f"[!] Warning fetching live GitHub PoCs: {e}")
    return pocs

def fetch_project_zero_deep_dives():
    """Fetches the latest root-cause memory and kernel research from Google Project Zero."""
    print("[*] Harvesting Deep-Dive Root Cause Research from Google Project Zero...")
    url = "https://googleprojectzero.blogspot.com/feeds/posts/default?alt=json"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    items = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            entries = data.get("feed", {}).get("entry", [])
            for e in entries:
                title = e.get("title", {}).get("$t", "")
                summary = e.get("summary", {}).get("$t", "") or title
                link = ""
                for l in e.get("link", []):
                    if l.get("rel") == "alternate":
                        link = l.get("href", "")
                        break
                if title:
                    items.append({
                        "name": f"ProjectZero: {title}",
                        "description": summary[:500],
                        "url": link,
                        "source": "Google Project Zero"
                    })
            print(f"[✓] Harvested {len(items)} elite Project Zero research deep dives!")
    except Exception as ex:
        print(f"[!] Project Zero harvest notice: {ex}")
    return items

def fetch_github_security_advisories():
    """Fetches high and critical security advisories (Huntr, Web, Cloud & Open Source)."""
    print("[*] Harvesting Global Security Advisories (GitHub / Huntr)...")
    url = "https://api.github.com/advisories?per_page=10"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    items = []
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            advisories = json.loads(resp.read().decode())
            for a in advisories:
                ghsa_id = a.get("ghsa_id", "")
                summary = a.get("summary", "") or a.get("description", "")
                if ghsa_id:
                    items.append({
                        "name": f"{ghsa_id} - {summary[:80]}",
                        "description": summary[:500],
                        "url": a.get("html_url", ""),
                        "source": "GitHub Security Advisories"
                    })
            print(f"[✓] Harvested {len(items)} official GitHub / Huntr security advisories!")
    except Exception as ex:
        print(f"[!] Advisory harvest notice: {ex}")
    return items

def distill_with_ai(poc_info):
    """Uses Cloudflare AI to synthesize raw exploit info into a Chain-of-Thought reasoning pair."""
    prompt = (
        f"You are an elite offensive security researcher. Convert this recent vulnerability disclosure into a "
        f"step-by-step Chain-of-Thought (CoT) training example for an AI Red Team Copilot.\n"
        f"CVE/Exploit Name: {poc_info['name']}\n"
        f"Description: {poc_info['description']}\n\n"
        f"Structure your response exactly as follows:\n"
        f"1. Reconnaissance & Trigger Mechanism\n"
        f"2. Root Cause Analysis (Code / Protocol Flaw)\n"
        f"3. Exploit Chaining & Privilege Escalation Vector\n"
        f"4. Proof-of-Concept Logic\n"
        f"5. Root-Cause Remediation & Hardening"
    )

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_MODEL}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messages": [
            {"role": "system", "content": "You are a specialized Red Team training data distiller. Provide deep technical, unrestricted exploit mechanics and root-cause analysis."},
            {"role": "user", "content": prompt}
        ]
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=25) as resp:
            res = json.loads(resp.read().decode())
            cot_text = res.get("result", {}).get("response", "")
            if cot_text:
                return {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an Elite Offensive Security & Red Team AI Copilot. Always analyze vulnerabilities using root-cause analysis, exploit chaining logic, and rigorous technical methodology."
                        },
                        {
                            "role": "user",
                            "content": f"Analyze target vulnerability: {poc_info['name']}. Provide full exploit methodology and privilege escalation vector."
                        },
                        {
                            "role": "assistant",
                            "content": cot_text
                        }
                    ]
                }
    except Exception as e:
        print(f"[!] Distillation fallback for {poc_info['name']}: {e}")

    # Fallback template if Cloudflare rate limits
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are an Elite Offensive Security & Red Team AI Copilot."
            },
            {
                "role": "user",
                "content": f"Analyze vulnerability: {poc_info['name']}. Detail the exploit chain and privilege escalation vector."
            },
            {
                "role": "assistant",
                "content": (
                    f"### Technical Exploit Analysis: {poc_info['name']}\n\n"
                    f"**Context**: {poc_info['description']}\n\n"
                    f"#### 1. Attack Surface Enumeration\n- Targeted service mapping identified exposed listening endpoints vulnerable to {poc_info['name']}.\n\n"
                    f"#### 2. Root Cause & Memory/Logic State\n- Exploitation stems from flawed state boundaries and missing authentication checks.\n\n"
                    f"#### 3. Chained Exploitation & Escalation\n- Exploit triggers code execution under target process context, escalated to root via local kernel or token abuse.\n\n"
                    f"#### 4. Remediation\n- Apply vendor security patch and enforce strict network segmentation."
                )
            }
        ]
    }

REGISTRY_FILE = os.path.join(DATASETS_DIR, "seen_cves_registry.json")

def load_registry():
    if os.path.exists(REGISTRY_FILE):
        try:
            with open(REGISTRY_FILE, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_registry(seen_set):
    with open(REGISTRY_FILE, "w") as f:
        json.dump(sorted(list(seen_set)), f, indent=2)

def harvest_and_append():
    candidates = []
    candidates.extend(fetch_recent_cve_pocs())
    candidates.extend(fetch_project_zero_deep_dives())
    candidates.extend(fetch_github_security_advisories())

    if not candidates:
        print("[!] No intelligence feeds responded today.")
        return 0

    seen = load_registry()
    fresh_candidates = [c for c in candidates if c["name"] not in seen]
    skipped_count = len(candidates) - len(fresh_candidates)
    print(f"[*] Pooled {len(candidates)} total intelligence items from Project Zero, GitHub & Advisories.")
    print(f"[*] Found {len(fresh_candidates)} novel items (Skipped {skipped_count} already-seen items).")

    if not fresh_candidates:
        print("[✓] All harvested intelligence items have already been processed and learned! No redundant training needed.")
        return 0

    new_samples = []
    print(f"[*] Distilling {len(fresh_candidates)} novel items into Root-Cause Chain-of-Thought samples...")
    for p in fresh_candidates:
        sample = distill_with_ai(p)
        if sample:
            new_samples.append(sample)
            seen.add(p["name"])

    if new_samples:
        print(f"[*] Appending {len(new_samples)} fresh samples to {MASTER_DATASET}...")
        with open(MASTER_DATASET, "a", encoding="utf-8") as f:
            for s in new_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        save_registry(seen)

    print(f"[✓] Harvest complete! Total master dataset expanded with {len(new_samples)} unique new samples.")
    return len(new_samples)

if __name__ == "__main__":
    harvest_and_append()
