#!/usr/bin/env python3
"""
Local Brain Gateway & Failover Proxy
Listens on http://127.0.0.1:8080/v1
Routes requests primarily to Kaggle GPU Server.
Automatically fails over to Hugging Face if Kaggle is offline.
Ensures zero-config changes for OpenHands, Cline, Antigravity, or any AI Agent!
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error
from http.server import HTTPServer, BaseHTTPRequestHandler

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gateway_config.json")
ENDPOINT_FILE = os.path.join(REPO_DIR, "data_pipeline", "active_endpoint.json")

def load_config():
    default_config = {
        "kaggle_url": None,
        "fallback_url": "https://mmossad2124-mossad-pentast-ai.hf.space/v1",
        "api_key": "sk-mossad-pentast-2026",
        "timeout_seconds": 15
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                cfg = {**default_config, **json.load(f)}
        except Exception:
            cfg = default_config
    else:
        cfg = default_config

    # Auto-detect from active_endpoint.json if available
    if not cfg.get("kaggle_url") and os.path.exists(ENDPOINT_FILE):
        try:
            with open(ENDPOINT_FILE, "r") as ef:
                ep_data = json.load(ef)
                u = ep_data.get("url")
                if u and "trycloudflare.com" in u:
                    cfg["kaggle_url"] = u
        except Exception:
            pass

    return cfg

def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[!] Error saving config: {e}")

class GatewayHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] [GATEWAY] {args[0]} - {args[1]}\n")

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        cfg = load_config()
        path = self.path

        if path in ["/", "/health"]:
            status_data = {
                "status": "online",
                "active_brain": "Kaggle GPU" if cfg.get("kaggle_url") else "Fallback",
                "kaggle_url": cfg.get("kaggle_url"),
                "fallback_url": cfg.get("fallback_url")
            }
            self._send_json(200, status_data)
            return

        if path == "/v1/models":
            models_data = {
                "object": "list",
                "data": [
                    {"id": "Mossad-pentast-ai", "object": "model", "owned_by": "mossad"}
                ]
            }
            self._send_json(200, models_data)
            return

        self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        cfg = load_config()
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        if self.path == "/set_kaggle_url":
            try:
                data = json.loads(body.decode("utf-8"))
                new_url = data.get("url")
                if new_url:
                    cfg["kaggle_url"] = new_url.rstrip("/")
                    save_config(cfg)
                    print(f"[*] Gateway updated Kaggle URL to: {new_url}")
                    self._send_json(200, {"status": "updated", "kaggle_url": new_url})
                    return
            except Exception as e:
                self._send_json(400, {"error": str(e)})
                return

        if self.path in ["/v1/chat/completions", "/chat/completions"]:
            self._handle_chat_completion(body, cfg)
            return

        self._send_json(404, {"error": "Endpoint not recognized by Gateway"})

    def _handle_chat_completion(self, body_bytes, cfg):
        # Auto-refresh endpoint from GitHub/file if kaggle_url is not set
        if not cfg.get("kaggle_url"):
            try:
                # Check GitHub raw
                gh_raw = "https://raw.githubusercontent.com/mmossad2124-blip/BugBounty-Copilot/main/data_pipeline/active_endpoint.json"
                req_gh = urllib.request.Request(gh_raw, headers={"User-Agent": "BrainGateway"})
                with urllib.request.urlopen(req_gh, timeout=4) as g_resp:
                    g_data = json.loads(g_resp.read().decode())
                    if g_data.get("url") and "trycloudflare.com" in g_data["url"]:
                        cfg["kaggle_url"] = g_data["url"]
                        save_config(cfg)
            except Exception:
                pass

        targets = []
        if cfg.get("kaggle_url"):
            k_base = cfg["kaggle_url"].rstrip("/")
            if not k_base.endswith("/v1"):
                k_url = f"{k_base}/v1/chat/completions"
            else:
                k_url = f"{k_base}/chat/completions"
            targets.append(("Kaggle GPU", k_url))

        if cfg.get("fallback_url"):
            fb_base = cfg["fallback_url"].rstrip("/")
            if not fb_base.endswith("/v1"):
                fb_url = f"{fb_base}/v1/chat/completions"
            else:
                fb_url = f"{fb_base}/chat/completions"
            targets.append(("HuggingFace Fallback", fb_url))

        for target_name, target_url in targets:
            try:
                print(f"[*] Forwarding prompt to {target_name}: {target_url}...")
                req = urllib.request.Request(
                    target_url,
                    data=body_bytes,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {cfg.get('api_key', 'sk-mossad-pentast-2026')}",
                        "User-Agent": "MossadBrainGateway/2.0"
                    }
                )
                with urllib.request.urlopen(req, timeout=cfg.get("timeout_seconds", 30)) as resp:
                    resp_data = resp.read()
                    self.send_response(resp.status)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.end_headers()
                    self.wfile.write(resp_data)
                    print(f"[✓] {target_name} responded successfully (HTTP {resp.status})!")
                    return
            except Exception as e:
                print(f"[!] Warning: {target_name} failed ({e}). Attempting next route...")

        err_msg = {
            "error": "All brain endpoints (Kaggle & Fallback) are currently unreachable.",
            "instructions": "Run ./start_session.sh to launch your Kaggle GPU brain."
        }
        self._send_json(503, err_msg)

    def _send_json(self, status_code, data):
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

def run_server(port=8080):
    server = HTTPServer(("0.0.0.0", port), GatewayHandler)
    print(f"\n{'='*70}")
    print(f"🚀 [MOSSAD BRAIN GATEWAY] Listening on http://0.0.0.0:{port}/v1 (Docker & Host accessible)")
    print(f"🔗 Any Agent (OpenHands, Cline, Antigravity) connects here with ZERO config changes!")
    print(f"{'='*70}\n")
    server.serve_forever()

if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
