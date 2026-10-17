#!/usr/bin/env python3
"""
Mossad-Pentast-AI Exclusive Brain Gateway & Cloud Linux Execution Proxy
Listens on http://0.0.0.0:8080/v1 (accessible by Host, Docker OpenHands, and CLI)
STRICT POLICY: ONLY routes to our own fine-tuned model (Mossad-pentast-ai).
Never uses external/third-party models.

Routing Hierarchy:
  1. Primary (Fast GPU + 10Gbps Cloud Linux VM): Active Kaggle GPU Server running Mossad-pentast-ai
     (auto-discovered via data_pipeline/active_endpoint.json or gateway_config.json)
  2. Secondary Fallback (Slower CPU/Space): Same trained model (Mossad-pentast-ai)
     hosted on Hugging Face Space / Secondary CPU Node.
"""

import json
import os
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gateway_config.json")
ENDPOINT_FILE = os.path.join(REPO_DIR, "data_pipeline", "active_endpoint.json")
HISTORY_DIR = os.path.join(REPO_DIR, "chat_history")
os.makedirs(HISTORY_DIR, exist_ok=True)
HISTORY_JSONL = os.path.join(HISTORY_DIR, "conversations.jsonl")
HISTORY_MD = os.path.join(HISTORY_DIR, "latest_chat.md")


def load_config():
    default_config = {
        "kaggle_url": None,
        "fallback_url": "https://mmossad2124-mossad-pentast-ai.hf.space/v1",
        "api_key": "sk-mossad-pentast-2026",
        "timeout_seconds": 180,
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = {**default_config, **json.load(f)}
        except Exception:
            cfg = default_config
    else:
        cfg = default_config

    # Auto-detect from active_endpoint.json if updated recently
    if os.path.exists(ENDPOINT_FILE):
        try:
            with open(ENDPOINT_FILE, "r", encoding="utf-8") as ef:
                ep_data = json.load(ef)
                u = ep_data.get("url")
                if u and "trycloudflare.com" in u and ep_data.get("status") == "ONLINE":
                    cfg["kaggle_url"] = u
        except Exception:
            pass

    return cfg


def save_config(cfg):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception as e:
        print(f"[!] Error saving config: {e}")


def log_chat_turn(user_msg: str, assistant_msg: str, backend_name: str):
    """Persist every conversation turn locally and in markdown for GitHub backup."""
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S")
        entry = {
            "timestamp": ts,
            "backend": backend_name,
            "user": user_msg,
            "assistant": assistant_msg,
        }
        with open(HISTORY_JSONL, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        with open(HISTORY_MD, "a", encoding="utf-8") as mf:
            mf.write(f"\n### 🕒 {ts} ({backend_name})\n")
            mf.write(f"**👤 المستخدم:**\n```text\n{user_msg}\n```\n")
            mf.write(f"**🤖 Mossad-pentast-ai:**\n```text\n{assistant_msg}\n```\n---\n")
    except Exception as e:
        print(f"[!] History log error: {e}")


def refresh_kaggle_url_from_github(cfg):
    try:
        gh_raw = f"https://raw.githubusercontent.com/mmossad2124-blip/BugBounty-Copilot/main/data_pipeline/active_endpoint.json?t={int(time.time())}"
        req_gh = urllib.request.Request(gh_raw, headers={"User-Agent": "BrainGateway/3.2", "Cache-Control": "no-cache"})
        with urllib.request.urlopen(req_gh, timeout=5) as g_resp:
            g_data = json.loads(g_resp.read().decode("utf-8"))
            if g_data.get("url") and "trycloudflare.com" in g_data["url"] and g_data.get("status") == "ONLINE":
                if cfg.get("kaggle_url") != g_data["url"]:
                    cfg["kaggle_url"] = g_data["url"]
                    save_config(cfg)
                    with open(ENDPOINT_FILE, "w", encoding="utf-8") as ef:
                        json.dump(g_data, ef, indent=2)
                    print(f"[✓] Auto-discovered new Kaggle GPU URL from GitHub: {cfg['kaggle_url']}")
    except Exception:
        pass
    return cfg


class GatewayHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        sys.stdout.write(f"[{time.strftime('%H:%M:%S')}] [GATEWAY] {args[0]}\n")
        sys.stdout.flush()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.end_headers()

    def do_GET(self):
        cfg = load_config()
        path = self.path.split("?")[0]

        if path in ["/", "/health", "/v1/health"]:
            status_data = {
                "status": "online",
                "model": "Mossad-pentast-ai (Exclusive Trained Weights)",
                "active_brain": "Kaggle GPU (Primary)" if cfg.get("kaggle_url") else "HuggingFace Fallback (Secondary)",
                "cloud_linux_vm": "ONLINE (10Gbps)" if cfg.get("kaggle_url") else "STANDBY",
                "kaggle_url": cfg.get("kaggle_url"),
                "fallback_url": cfg.get("fallback_url"),
            }
            self._send_json(200, status_data)
            return

        if path in ["/v1/models", "/models"]:
            models_data = {
                "object": "list",
                "data": [
                    {
                        "id": "Mossad-pentast-ai",
                        "object": "model",
                        "created": 1700000000,
                        "owned_by": "mossad",
                    },
                    {
                        "id": "openai/Mossad-pentast-ai",
                        "object": "model",
                        "created": 1700000000,
                        "owned_by": "mossad",
                    },
                ],
            }
            self._send_json(200, models_data)
            return

        self._send_json(404, {"error": "Not Found"})

    def do_POST(self):
        cfg = load_config()
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"
        path = self.path.split("?")[0]

        if path == "/set_kaggle_url":
            try:
                data = json.loads(body.decode("utf-8"))
                new_url = data.get("url")
                if new_url:
                    cfg["kaggle_url"] = new_url.rstrip("/")
                    save_config(cfg)
                    self._send_json(200, {"status": "updated", "kaggle_url": new_url})
                    return
            except Exception as e:
                self._send_json(400, {"error": str(e)})
                return

        if path in ["/execute", "/v1/execute"]:
            self._handle_cloud_execute(body, cfg)
            return

        if path in ["/v1/chat/completions", "/chat/completions"]:
            self._handle_chat_completion(body, cfg)
            return

        self._send_json(404, {"error": f"Endpoint {path} not recognized by Gateway"})

    def _handle_cloud_execute(self, body_bytes, cfg):
        """Forward bash commands to the 10Gbps Cloud Linux VM on Kaggle."""
        try:
            req_json = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            self._send_json(400, {"error": "Invalid JSON"})
            return

        if not cfg.get("kaggle_url"):
            cfg = refresh_kaggle_url_from_github(cfg)

        k_url = cfg.get("kaggle_url", "")
        if k_url:
            base_root = k_url[:-3] if k_url.endswith("/v1") else k_url.rstrip("/")
            exec_url = f"{base_root}/execute"
            try:
                cmd_str = req_json.get("command", "")
                print(f"[☁️ CLOUD EXEC] Forwarding command to Cloud Linux VM (10Gbps): {cmd_str[:80]}...")
                req = urllib.request.Request(
                    exec_url,
                    data=json.dumps(req_json).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "MossadBrainGateway/3.2"},
                    method="POST",
                )
                timeout_s = int(req_json.get("timeout", 120)) + 15
                with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                    resp_obj = json.loads(resp.read().decode("utf-8"))
                    self._send_json(200, resp_obj)
                    return
            except Exception as e:
                print(f"[!] Cloud Linux VM execute warning: {e}")

        self._send_json(503, {"error": "Cloud Linux VM unreachable", "status": "offline"})

    def _handle_chat_completion(self, body_bytes, cfg):
        try:
            req_json = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            req_json = {}

        is_stream = bool(req_json.get("stream", False))
        last_user_text = ""

        # Flatten list-type content blocks if sent by OpenHands/LiteLLM
        if "messages" in req_json and isinstance(req_json["messages"], list):
            clean_msgs = []
            for m in req_json["messages"]:
                role = m.get("role", "user")
                content = m.get("content", "")
                if isinstance(content, list):
                    parts = []
                    for p in content:
                        if isinstance(p, dict) and p.get("type") == "text":
                            parts.append(p.get("text", ""))
                        elif isinstance(p, str):
                            parts.append(p)
                    content = "\n".join(parts)
                content_str = str(content)
                if role == "user":
                    last_user_text = content_str
                clean_msgs.append({"role": role, "content": content_str})
            req_json["messages"] = clean_msgs

        # Always force stream=False to backend and convert to SSE if client requested stream=True
        backend_req = dict(req_json)
        backend_req["stream"] = False
        backend_bytes = json.dumps(backend_req).encode("utf-8")

        # Refresh Kaggle URL from GitHub if not set
        if not cfg.get("kaggle_url"):
            cfg = refresh_kaggle_url_from_github(cfg)

        targets = []
        if cfg.get("kaggle_url"):
            k_base = cfg["kaggle_url"].rstrip("/")
            k_url = f"{k_base}/chat/completions" if k_base.endswith("/v1") else f"{k_base}/v1/chat/completions"
            targets.append(("1. Primary Kaggle GPU (Mossad-pentast-ai)", k_url))

        if cfg.get("fallback_url"):
            fb_base = cfg["fallback_url"].rstrip("/")
            fb_url = f"{fb_base}/chat/completions" if fb_base.endswith("/v1") else f"{fb_base}/v1/chat/completions"
            targets.append(("2. Secondary HuggingFace Space (Mossad-pentast-ai)", fb_url))

        for target_name, target_url in targets:
            try:
                print(f"[*] Forwarding prompt to {target_name}: {target_url}...")
                req = urllib.request.Request(
                    target_url,
                    data=backend_bytes,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {cfg.get('api_key', 'sk-mossad-pentast-2026')}",
                        "User-Agent": "MossadBrainGateway/3.2",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=cfg.get("timeout_seconds", 180)) as resp:
                    resp_data = resp.read().decode("utf-8")
                    resp_obj = json.loads(resp_data)
                    if "choices" in resp_obj:
                        reply_text = resp_obj["choices"][0].get("message", {}).get("content", "")
                        print(f"[✓] {target_name} responded ({len(reply_text)} chars)!")
                        log_chat_turn(last_user_text[-500:], reply_text, target_name)
                        self._send_openai_response(resp_obj, is_stream)
                        return
            except Exception as e:
                print(f"[!] Warning: {target_name} unreachable ({e}).")
                if "Primary Kaggle" in target_name:
                    old_url = cfg.get("kaggle_url")
                    cfg = refresh_kaggle_url_from_github(cfg)
                    if cfg.get("kaggle_url") and cfg.get("kaggle_url") != old_url:
                        new_base = cfg["kaggle_url"].rstrip("/")
                        new_url = f"{new_base}/chat/completions" if new_base.endswith("/v1") else f"{new_base}/v1/chat/completions"
                        try:
                            req2 = urllib.request.Request(
                                new_url,
                                data=backend_bytes,
                                headers={
                                    "Content-Type": "application/json",
                                    "Authorization": f"Bearer {cfg.get('api_key', 'sk-mossad-pentast-2026')}",
                                    "User-Agent": "MossadBrainGateway/3.2",
                                },
                                method="POST",
                            )
                            with urllib.request.urlopen(req2, timeout=cfg.get("timeout_seconds", 180)) as resp2:
                                resp_obj2 = json.loads(resp2.read().decode("utf-8"))
                                if "choices" in resp_obj2:
                                    reply_text = resp_obj2["choices"][0].get("message", {}).get("content", "")
                                    print("[✓] Refreshed Kaggle GPU URL responded successfully!")
                                    log_chat_turn(last_user_text[-500:], reply_text, target_name)
                                    self._send_openai_response(resp_obj2, is_stream)
                                    return
                        except Exception:
                            pass

        err_msg = {
            "error": {
                "message": "Mossad-pentast-ai endpoints (1. Kaggle GPU & 2. HuggingFace Space) are currently starting or offline.",
                "type": "server_error",
            }
        }
        self._send_json(503, err_msg)

    def _send_openai_response(self, openai_resp: dict, is_stream: bool):
        if not is_stream:
            self._send_json(200, openai_resp)
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        content = openai_resp["choices"][0]["message"]["content"]
        chunk_id = openai_resp.get("id", "chatcmpl-mossad")
        model_name = openai_resp.get("model", "Mossad-pentast-ai")

        chunk_data = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "delta": {"role": "assistant", "content": content},
                    "finish_reason": None,
                }
            ],
        }
        stop_data = {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": int(time.time()),
            "model": model_name,
            "choices": [
                {
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop",
                }
            ],
        }
        self.wfile.write(f"data: {json.dumps(chunk_data)}\n\n".encode("utf-8"))
        self.wfile.write(f"data: {json.dumps(stop_data)}\n\n".encode("utf-8"))
        self.wfile.write(b"data: [DONE]\n\n")
        self.wfile.flush()

    def _send_json(self, status_code, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(payload)


def _background_endpoint_watcher():
    while True:
        try:
            cfg = load_config()
            refresh_kaggle_url_from_github(cfg)
        except Exception:
            pass
        time.sleep(10)


def run_server(port=8080):
    watcher = threading.Thread(target=_background_endpoint_watcher, daemon=True)
    watcher.start()
    server = ThreadingHTTPServer(("0.0.0.0", port), GatewayHandler)
    print(f"\n{'='*70}")
    print(f"🚀 [MOSSAD BRAIN GATEWAY - EXCLUSIVE] Listening on http://0.0.0.0:{port}/v1")
    print(f"🔗 1. Primary: Kaggle GPU (Mossad-pentast-ai) | 2. Fallback: Hugging Face (Mossad-pentast-ai)")
    print(f"☁️  Cloud Linux Execution Proxy enabled at http://0.0.0.0:{port}/execute")
    print(f"{'='*70}\n")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
