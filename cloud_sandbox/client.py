#!/usr/bin/env python3
"""
CLI & Python Bridge to execute commands remotely on GitHub Codespaces Cloud Sandbox (Port 8000).
Usage:
  python3 cloud_sandbox/client.py --set-url https://<your-codespace>-8000.app.github.dev
  python3 cloud_sandbox/client.py "nmap -F scanme.nmap.org"
"""

import json
import os
import sys
import urllib.request

CONFIG_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "automation",
    "gateway_config.json",
)


def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def save_config(cfg):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def run_remote_command(cmd: str, timeout: int = 120):
    cfg = load_config()
    sandbox_url = os.environ.get("CODESPACE_SANDBOX_URL") or cfg.get("codespace_sandbox_url", "")
    api_key = cfg.get("api_key", "sk-mossad-pentast-2026")

    if not sandbox_url:
        print("[!] No GitHub Codespace Sandbox URL configured yet.")
        print("    Set it once via: python3 cloud_sandbox/client.py --set-url https://<codespace-name>-8000.app.github.dev")
        sys.exit(1)

    endpoint = sandbox_url.rstrip("/") + "/execute"
    payload = json.dumps({"command": cmd, "timeout": timeout}).encode("utf-8")
    req = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout + 10) as resp:
        result = json.loads(resp.read().decode("utf-8"))
        if result.get("stdout"):
            print(result["stdout"], end="")
        if result.get("stderr"):
            print(result["stderr"], file=sys.stderr, end="")
        return result


if __name__ == "__main__":
    if len(sys.argv) >= 3 and sys.argv[1] == "--set-url":
        new_url = sys.argv[2].strip().rstrip("/")
        cfg = load_config()
        cfg["codespace_sandbox_url"] = new_url
        save_config(cfg)
        print(f"[✓] GitHub Codespace Sandbox URL saved: {new_url}")
        sys.exit(0)

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 cloud_sandbox/client.py --set-url https://<your-codespace>-8000.app.github.dev")
        print("  python3 cloud_sandbox/client.py \"<command>\"")
        sys.exit(1)

    command_str = " ".join(sys.argv[1:])
    run_remote_command(command_str)
