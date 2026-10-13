#!/usr/bin/env python3
"""
Cloud Agent Runner
Orchestrates the deployment of HexStrike AI Docker sandbox and Streamlit Web UI in the cloud.
Exposes a secure public URL via Cloudflare Tunnel for interactive user sessions.
"""

import os
import sys
import time
import subprocess
import json

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def start_hexstrike_cloud_agent():
    print(f"\n{'='*75}")
    print("🚀 [CLOUD SANDBOX] Launching BugBounty-Copilot & HexStrike AI...")
    print(f"{'='*75}")

    dockerfile = os.path.join(REPO_DIR, "docker", "Dockerfile.cloud_agent")
    
    # 1. Build Docker image
    print("[*] Building 100% isolated Docker sandbox...")
    build_cmd = ["docker", "build", "-t", "bugbounty-cloud-agent", "-f", dockerfile, REPO_DIR]
    subprocess.run(build_cmd, check=True)

    # 2. Run Container
    print("[*] Starting HexStrike Server & Agent UI Container...")
    run_cmd = [
        "docker", "run", "-d",
        "--name", "agent-sandbox-instance",
        "-p", "8501:8501", "-p", "5055:5055",
        "bugbounty-cloud-agent"
    ]
    subprocess.run(run_cmd, check=True)
    time.sleep(8)

    # 3. Setup Cloudflare Tunnel for secure public URL
    print("[*] Initializing Cloudflare Tunnel for Public Web Access...")
    cf_bin = "/tmp/cloudflared"
    if not os.path.exists(cf_bin):
        subprocess.run(["curl", "-sL", "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64", "-o", cf_bin], check=True)
        os.chmod(cf_bin, 0o755)

    tunnel_proc = subprocess.Popen([cf_bin, "tunnel", "--url", "http://localhost:8501"], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
    
    print("\n" + "="*75)
    print("🌐 WAITING FOR PUBLIC TUNNEL URL...")
    print("="*75)
    
    time.sleep(8)
    # Read output to extract url
    for _ in range(15):
        line = tunnel_proc.stderr.readline()
        if "trycloudflare.com" in line:
            import re
            m = re.search(r"https://[a-zA-Z0-9-]+\.trycloudflare\.com", line)
            if m:
                url = m.group(0)
                print(f"\n🎉 [SUCCESS] WEB CHAT UI IS LIVE: {url}\n")
                print("Open the link above in your browser to interact with the model and HexStrike AI!\n")
                break
        time.sleep(1)

if __name__ == "__main__":
    start_hexstrike_cloud_agent()
