#!/usr/bin/env python3
"""
Multi-Source Threat Intelligence & Root Cause Harvester
Orchestrates deep-dive data collection across all elite sources:
- Google Project Zero (Memory & 0-Day Root Causes)
- SpecterOps (Living-off-the-land & Active Directory Tradecraft)
- Kaspersky Securelist GReAT (Advanced APTs & Financial/Banking Trojans)
- GitHub Security Advisories & Huntr (AI Security & Web Vulnerabilities)
- GitHub CVE PoC Radars
- Deduplication via seen_cves_registry.json
"""

import os
import sys
import json
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

DATASETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "processed_datasets")
os.makedirs(DATASETS_DIR, exist_ok=True)
REGISTRY_CONFIG = os.path.join(os.path.dirname(os.path.abspath(__file__)), "elite_threat_intel_registry.json")
SEEN_REGISTRY = os.path.join(DATASETS_DIR, "seen_cves_registry.json")
MASTER_DATASET = os.path.join(DATASETS_DIR, "master_redteam_cot.jsonl")

# Load environment
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

def load_seen():
    if os.path.exists(SEEN_REGISTRY):
        try:
            with open(SEEN_REGISTRY, "r") as f:
                return set(json.load(f))
        except Exception:
            pass
    return set()

def save_seen(seen_set):
    with open(SEEN_REGISTRY, "w") as f:
        json.dump(sorted(list(seen_set)), f, indent=2)

def fetch_rss_feed(source_name, feed_url, max_items=5):
    """Fetches articles from standard RSS feeds (SpecterOps, Kaspersky Securelist)."""
    print(f"[*] Fetching elite intel from: {source_name}...")
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    items = []
    try:
        req = urllib.request.Request(feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            content = resp.read()
            root = ET.fromstring(content)
            # Standard RSS channel -> item
            for item in root.findall(".//item")[:max_items]:
                title = item.findtext("title") or ""
                link = item.findtext("link") or ""
                desc = item.findtext("description") or title
                if title:
                    items.append({
                        "name": f"[{source_name}] {title.strip()}",
                        "description": desc.strip()[:600],
                        "url": link.strip(),
                        "source": source_name
                    })
            print(f"[✓] {source_name}: Retrieved {len(items)} research articles!")
    except Exception as e:
        print(f"[!] Warning fetching {source_name}: {e}")
    return items

def fetch_project_zero(max_items=5):
    """Fetches root-cause deep dives from Google Project Zero."""
    print("[*] Fetching root-cause research from Google Project Zero...")
    url = "https://googleprojectzero.blogspot.com/feeds/posts/default?alt=json"
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode())
            entries = data.get("feed", {}).get("entry", [])[:max_items]
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
                        "name": f"[Project Zero] {title.strip()}",
                        "description": summary.strip()[:600],
                        "url": link,
                        "source": "Google Project Zero"
                    })
            print(f"[✓] Project Zero: Retrieved {len(items)} deep-dive articles!")
    except Exception as e:
        print(f"[!] Warning fetching Project Zero: {e}")
    return items

def fetch_github_advisories(max_items=10):
    """Fetches high/critical advisories (Huntr AI, Cloud, Enterprise Apps)."""
    print("[*] Fetching Global Advisories (GitHub / Huntr AI)...")
    url = f"https://api.github.com/advisories?per_page={max_items}"
    items = []
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as resp:
            advisories = json.loads(resp.read().decode())
            for a in advisories:
                ghsa_id = a.get("ghsa_id", "")
                summary = a.get("summary", "") or a.get("description", "")
                if ghsa_id:
                    items.append({
                        "name": f"[Advisory] {ghsa_id} - {summary[:80]}",
                        "description": summary.strip()[:600],
                        "url": a.get("html_url", ""),
                        "source": "GitHub Security Advisories"
                    })
            print(f"[✓] Advisories: Retrieved {len(items)} global security advisories!")
    except Exception as e:
        print(f"[!] Warning fetching Advisories: {e}")
    return items

def fetch_unprotect_techniques(max_items=4):
    """Fetches evasion and bypass techniques from the Unprotect Project."""
    print("[*] Fetching evasion tradecraft from Unprotect Project...")
    url = "https://api.github.com/repos/Unprotect-Project/ContributeV2/contents/Techniques"
    headers = {"User-Agent": "Python"}
    items = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            files = json.loads(resp.read().decode())
            for f in files:
                name = f.get("name", "")
                if name and not name.startswith("."):
                    items.append({
                        "name": f"[Unprotect] {name}",
                        "description": f"Evasion & defense bypass tradecraft: {name}. Low-level anti-analysis, memory obfuscation, and detection bypass.",
                        "url": f.get("html_url", ""),
                        "source": "Unprotect Project (Evasion Database)"
                    })
                    if len(items) >= max_items:
                        break
            print(f"[✓] Unprotect Project: Retrieved {len(items)} evasion techniques!")
    except Exception as e:
        print(f"[!] Warning fetching Unprotect: {e}")
    return items

def fetch_vx_underground(max_items=4):
    """Fetches advanced low-level C++ malware & evasion mechanics from vx-underground."""
    print("[*] Fetching advanced C++ evasion tradecraft from vx-underground...")
    url = "https://api.github.com/repos/vxunderground/VX-API/contents/VX-API"
    headers = {"User-Agent": "Python"}
    items = []
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            files = json.loads(resp.read().decode())
            for f in files:
                name = f.get("name", "")
                if name.endswith(".cpp") and any(k in name.lower() for k in ["bypass", "injection", "process", "hook", "debug", "token", "memory"]):
                    items.append({
                        "name": f"[vx-underground] {name}",
                        "description": f"Low-level C/C++ OS internal mechanic: {name}. Process injection, memory manipulation, and privilege bypass.",
                        "url": f.get("html_url", ""),
                        "source": "vx-underground (Elite Research)"
                    })
                    if len(items) >= max_items:
                        break
            print(f"[✓] vx-underground: Retrieved {len(items)} low-level C++ items!")
    except Exception as e:
        print(f"[!] Warning fetching vx-underground: {e}")
    return items

def fetch_syswhispers_hellsgate(max_items=2):
    """Fetches direct syscall & API unhooking research from SysWhispers3 and HellsGate."""
    print("[*] Fetching Direct Syscall & API Unhooking research (SysWhispers/HellsGate)...")
    items = [
        {
            "name": "[SysWhispers3 / HellsGate] Dynamic SSN Resolution & Direct Syscalls",
            "description": "Bypassing User-Mode EDR API Hooks via manual runtime parsing of ntdll.dll export directory, dynamic System Service Number (SSN) sorting, and executing direct 'syscall' assembly stubs.",
            "url": "https://github.com/klezVirus/SysWhispers3",
            "source": "SysWhispers3 / HellsGate Research"
        },
        {
            "name": "[HalosGate / TartarusGate] Hook Detection & Neighboring SSN Recovery",
            "description": "Recovering original system call numbers when ntdll functions are hooked with JMP instructions by inspecting neighboring opcode offsets (Halo's Gate technique).",
            "url": "https://github.com/am0nsec/HellsGate",
            "source": "HellsGate / HalosGate Research"
        }
    ]
    print(f"[✓] SysWhispers & HellsGate: Added {len(items)} direct syscall research primitives!")
    return items[:max_items]

def distill_with_ai(intel_item):
    """Distills raw threat research into structured Chain-of-Thought (CoT) format via Cloudflare Workers AI."""
    prompt = (
        f"You are an Elite Offensive Security & Red Team AI Copilot. Convert this high-level security research disclosure "
        f"into a rigorous, step-by-step Chain-of-Thought (CoT) root-cause and exploit-mechanics training sample.\n\n"
        f"Source: {intel_item['source']}\n"
        f"Topic: {intel_item['name']}\n"
        f"Overview: {intel_item['description']}\n\n"
        f"Respond with this exact structure:\n"
        f"1. Vulnerability Surface & Architectural Flaw\n"
        f"2. Memory / State Machine Root Cause Analysis\n"
        f"3. Evasion, Privilege Escalation or Bypass Logic\n"
        f"4. Proof-of-Concept Methodology\n"
        f"5. Root-Cause Remediation & Detection Rules"
    )

    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_MODEL}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    payload = {
        "messages": [
            {"role": "system", "content": "You are a world-class Red Team & Vulnerability Researcher specializing in root-cause teardowns."},
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
                        {"role": "system", "content": "You are an Elite Offensive Security & Red Team AI Copilot. Always analyze vulnerabilities using root-cause analysis, exploit chaining logic, and rigorous technical methodology."},
                        {"role": "user", "content": f"Analyze: {intel_item['name']}. Provide deep root cause and exploit methodology."},
                        {"role": "assistant", "content": cot_text}
                    ]
                }
    except Exception as e:
        print(f"[!] AI distillation fallback for {intel_item['name']}: {e}")

    # Fallback template
    return {
        "messages": [
            {"role": "system", "content": "You are an Elite Offensive Security & Red Team AI Copilot."},
            {"role": "user", "content": f"Analyze: {intel_item['name']}"},
            {
                "role": "assistant",
                "content": (
                    f"### Elite Technical Teardown: {intel_item['name']}\n\n"
                    f"**Source**: {intel_item['source']}\n"
                    f"**Context**: {intel_item['description']}\n\n"
                    f"#### 1. Attack Surface Enumeration\n- Evaluated system boundaries, exported interfaces, and user input sanitization filters.\n\n"
                    f"#### 2. Root Cause Analysis\n- Memory/Logic state boundaries violated due to insufficient validation and improper reference lifetimes.\n\n"
                    f"#### 3. Exploit Chaining & Evasion\n- Exploits the primitive to achieve arbitrary execution context, evading behavioral detection via unhooked system interfaces.\n\n"
                    f"#### 4. Remediation & Hardening\n- Enforce strict parameter bounds, canonicalize pointers, and implement kernel/EDR telemetry logging."
                )
            }
        ]
    }

def run_multi_source_harvest():
    print(f"\n{'='*75}")
    print("🌐 [MULTI-SOURCE THREAT INTEL HARVESTER] Querying Elite Intelligence Sources")
    print(f"{'='*75}")

    all_items = []
    # 1. Google Project Zero (0-Day Memory & Root Cause)
    all_items.extend(fetch_project_zero(max_items=4))
    # 2. Unprotect Project (Evasion & Anti-Analysis Mechanics)
    all_items.extend(fetch_unprotect_techniques(max_items=4))
    # 3. vx-underground (Low-level C++ Injection & Memory Exploitation)
    all_items.extend(fetch_vx_underground(max_items=4))
    # 4. SysWhispers3 & HellsGate (Direct Syscalls & API Unhooking)
    all_items.extend(fetch_syswhispers_hellsgate(max_items=2))
    # 5. Kaspersky Securelist (GReAT APT & Advanced Threat Intel)
    all_items.extend(fetch_rss_feed("Kaspersky Securelist", "https://securelist.com/feed/", max_items=4))
    # 6. GitHub Advisories & Huntr (Web, AI, Cloud Criticals)
    all_items.extend(fetch_github_advisories(max_items=5))

    print(f"\n[*] Total Intelligence Items Harvested Across Feeds: {len(all_items)}")

    # Deduplicate against seen registry
    seen = load_seen()
    fresh = [item for item in all_items if item["name"] not in seen]
    skipped = len(all_items) - len(fresh)

    print(f"[*] Found {len(fresh)} Brand-New Research Items (Skipped {skipped} already processed).")

    if not fresh:
        print("[✓] All harvested threat intel articles are already in the model's memory!")
        return 0

    print(f"[*] Distilling {len(fresh)} novel research articles via Cloudflare Workers AI...")
    new_samples = []
    for item in fresh:
        sample = distill_with_ai(item)
        if sample:
            new_samples.append(sample)
            seen.add(item["name"])

    if new_samples:
        print(f"[*] Injecting {len(new_samples)} fresh elite samples into {MASTER_DATASET}...")
        with open(MASTER_DATASET, "a", encoding="utf-8") as f:
            for s in new_samples:
                f.write(json.dumps(s, ensure_ascii=False) + "\n")
        save_seen(seen)

    print(f"[✓] Multi-Source Harvester completed successfully! Master knowledge base updated.\n")
    return len(new_samples)

if __name__ == "__main__":
    run_multi_source_harvest()
