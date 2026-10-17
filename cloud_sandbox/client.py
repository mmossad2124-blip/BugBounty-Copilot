#!/usr/bin/env python3
"""
Unified Cloud & Local Sandbox Execution Bridge
Automatically routes cyber reconnaissance & development commands to:
  1. GitHub Codespaces Cloud Sandbox (if active)
  2. Kaggle 10Gbps Cloud VM Sandbox (if active)
  3. Local OpenHands Docker Sandbox (instant automatic fallback)
"""

import json
import os
import subprocess
import sys
import time
import urllib.request

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_PATH = os.path.join(REPO_DIR, "automation", "gateway_config.json")
ENDPOINT_PATH = os.path.join(REPO_DIR, "data_pipeline", "active_endpoint.json")


def load_config():
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def run_command_unified(cmd: str, timeout: int = 120):
    cfg = load_config()
    api_key = cfg.get("api_key", "sk-mossad-pentast-2026")

    # Candidate remote cloud sandboxes
    remote_targets = []
    cs_url = os.environ.get("CODESPACE_SANDBOX_URL") or cfg.get("codespace_sandbox_url")
    if cs_url:
        remote_targets.append(("GitHub Codespaces Cloud VM", cs_url.rstrip("/") + "/execute"))

    if os.path.exists(ENDPOINT_PATH):
        try:
            ep = json.load(open(ENDPOINT_PATH, "r", encoding="utf-8"))
            if ep.get("status") == "ONLINE" and ep.get("url"):
                remote_targets.append(("Kaggle 10Gbps Cloud VM", ep["url"].rstrip("/") + "/execute"))
        except Exception:
            pass

    for name, url in remote_targets:
        try:
            payload = json.dumps({"command": cmd, "timeout": timeout}).encode("utf-8")
            req = urllib.request.Request(
                url,
                data=payload,
                headers={"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=timeout + 5) as resp:
                res = json.loads(resp.read().decode("utf-8"))
                print(f"[⚡ Executed on {name} in {res.get('elapsed_seconds', 0)}s]")
                if res.get("stdout"):
                    print(res["stdout"], end="")
                if res.get("stderr"):
                    print(res["stderr"], file=sys.stderr, end="")
                return res
        except Exception:
            pass

    # Fallback: Execute inside OpenHands Isolated Docker Sandbox
    start_t = time.time()
    proc = subprocess.run(
        ["docker", "exec", "openhands-app", "bash", "-c", f"cd /opt/workspace_base && {cmd}"],
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    elapsed = round(time.time() - start_t, 2)
    print(f"[🐳 Executed in Local OpenHands Docker Sandbox in {elapsed}s]")
    if proc.stdout:
        print(proc.stdout, end="")
    if proc.stderr:
        print(proc.stderr, file=sys.stderr, end="")
    return {
        "status": "completed",
        "backend": "OpenHands Docker Sandbox",
        "exit_code": proc.returncode,
        "stdout": proc.stdout,
        "stderr": proc.stderr,
        "elapsed_seconds": elapsed,
    }


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--set-url":
        new_url = sys.argv[2].strip().rstrip("/")
        cfg = load_config()
        cfg["codespace_sandbox_url"] = new_url
        save_config(cfg)
        print(f"[✓] GitHub Codespace Sandbox URL saved: {new_url}")
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage: python3 cloud_sandbox/client.py \"<command>\"")
        sys.exit(1)

    run_command_unified(" ".join(sys.argv[1:]))
