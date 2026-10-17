#!/usr/bin/env python3
"""
Mossad-Pentast-AI Multi-Tier Brain Gateway & Failover Proxy
Listens on http://0.0.0.0:8080/v1 (accessible by Host, Docker OpenHands, and CLI)
Routing Hierarchy:
  1. Primary: Kaggle T4 GPU Server (Standalone 16-bit Mossad-pentast-ai) when active
  2. Instant 24/7 Failover: 3-Account Cloud GPU Cluster (Qwen2.5-Coder-32B & Llama-3.3-70B)
     using stored credentials in accounts/account_*.json — zero downtime, zero GPU quota burn when idle!
"""

import glob
import json
import os
import sys
import time
import urllib.error
import urllib.request
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gateway_config.json")
ENDPOINT_FILE = os.path.join(REPO_DIR, "data_pipeline", "active_endpoint.json")
ACCOUNTS_DIR = os.path.join(REPO_DIR, "accounts")

MOSSAD_SYSTEM_IDENTITY = (
    "You are Mossad-pentast-ai, an advanced autonomous AI cybersecurity & full-stack software engineering agent "
    "created and fine-tuned by Mossad (mmossad2124). You have full access to a Linux terminal, HexStrike AI security tools "
    "(nmap, nuclei, sqlmap, nikto, gobuster, ffuf, whois, dig, curl, python3), and workspace files. "
    "When running inside OpenHands (CodeActAgent), follow its exact XML/action format (<execute_bash>, etc.) whenever you need to run commands. "
    "Respond in the language used by the user (Arabic or English) accurately and concisely."
)


def load_cloud_accounts():
    accounts = []
    for path in sorted(glob.glob(os.path.join(ACCOUNTS_DIR, "account_*.json"))):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                cf = data.get("credentials", {}).get("cloudflare", {})
                if cf.get("account_id") and cf.get("api_token"):
                    accounts.append({
                        "username": data.get("username", "unknown"),
                        "account_id": cf["account_id"],
                        "api_token": cf["api_token"],
                    })
        except Exception:
            pass
    return accounts


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
            accounts = load_cloud_accounts()
            status_data = {
                "status": "online",
                "model": "Mossad-pentast-ai",
                "active_brain": "Kaggle GPU + 3-Account Cloud Cluster",
                "kaggle_url": cfg.get("kaggle_url"),
                "cloud_accounts_loaded": len(accounts),
                "codespace_sandbox_url": cfg.get("codespace_sandbox_url"),
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

        if path in ["/v1/chat/completions", "/chat/completions"]:
            self._handle_chat_completion(body, cfg)
            return

        self._send_json(404, {"error": f"Endpoint {path} not recognized by Gateway"})

    def _handle_chat_completion(self, body_bytes, cfg):
        try:
            req_json = json.loads(body_bytes.decode("utf-8"))
        except Exception:
            req_json = {}

        is_stream = bool(req_json.get("stream", False))

        # 1. Try Primary Kaggle GPU Tunnel if configured and reachable
        if cfg.get("kaggle_url"):
            k_base = cfg["kaggle_url"].rstrip("/")
            k_url = f"{k_base}/chat/completions" if k_base.endswith("/v1") else f"{k_base}/v1/chat/completions"
            try:
                # Fast non-streaming request to Kaggle
                k_payload = dict(req_json)
                k_payload["stream"] = False
                req = urllib.request.Request(
                    k_url,
                    data=json.dumps(k_payload).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {cfg.get('api_key', 'sk-mossad-pentast-2026')}",
                        "User-Agent": "MossadBrainGateway/3.0",
                    },
                )
                with urllib.request.urlopen(req, timeout=8) as resp:
                    resp_bytes = resp.read()
                    resp_obj = json.loads(resp_bytes.decode("utf-8"))
                    if "choices" in resp_obj:
                        print("[✓] Kaggle GPU Brain responded!")
                        self._send_openai_response(resp_obj, is_stream)
                        return
            except Exception as e:
                print(f"[*] Kaggle tunnel inactive ({e}). Failing over to 24/7 Cloud Cluster...")

        # 2. Instant Failover to 3-Account Cloud Cluster (Qwen2.5-Coder-32B / Llama-3.3-70B)
        accounts = load_cloud_accounts()
        raw_messages = req_json.get("messages", [])
        norm_messages = []
        has_system = False
        for m in raw_messages:
            role = m.get("role", "user")
            content = m.get("content", "")
            if isinstance(content, list):
                text_parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        text_parts.append(part.get("text", ""))
                    elif isinstance(part, str):
                        text_parts.append(part)
                content = "\n".join(text_parts)
            if role == "system":
                has_system = True
                content = MOSSAD_SYSTEM_IDENTITY + "\n\n" + str(content)
            norm_messages.append({"role": role, "content": str(content)})

        if not has_system:
            norm_messages.insert(0, {"role": "system", "content": MOSSAD_SYSTEM_IDENTITY})

        models_to_try = [
            "@cf/qwen/qwen2.5-coder-32b-instruct",
            "@cf/meta/llama-3.3-70b-instruct-fp8-fast",
            "@cf/meta/llama-3.1-8b-instruct",
        ]

        for acc in accounts:
            for cf_model in models_to_try:
                cf_url = f"https://api.cloudflare.com/client/v4/accounts/{acc['account_id']}/ai/run/{cf_model}"
                cf_payload = {
                    "messages": norm_messages,
                    "max_tokens": min(int(req_json.get("max_tokens") or 2048), 4096),
                    "temperature": float(req_json.get("temperature") or 0.2),
                }
                try:
                    req = urllib.request.Request(
                        cf_url,
                        data=json.dumps(cf_payload).encode("utf-8"),
                        headers={
                            "Authorization": f"Bearer {acc['api_token']}",
                            "Content-Type": "application/json",
                            "User-Agent": "MossadBrainGateway/3.0",
                        },
                        method="POST",
                    )
                    with urllib.request.urlopen(req, timeout=60) as resp:
                        raw_cf = json.loads(resp.read().decode("utf-8"))
                        res_block = raw_cf.get("result", {})
                        reply_text = ""
                        if isinstance(res_block, dict):
                            if "choices" in res_block and res_block["choices"]:
                                reply_text = res_block["choices"][0].get("message", {}).get("content", "")
                            if not reply_text:
                                reply_text = res_block.get("response", "")
                        if reply_text:
                            openai_resp = {
                                "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
                                "object": "chat.completion",
                                "created": int(time.time()),
                                "model": req_json.get("model", "Mossad-pentast-ai"),
                                "choices": [
                                    {
                                        "index": 0,
                                        "message": {
                                            "role": "assistant",
                                            "content": reply_text,
                                        },
                                        "finish_reason": "stop",
                                    }
                                ],
                                "usage": res_block.get(
                                    "usage",
                                    {"prompt_tokens": 100, "completion_tokens": 100, "total_tokens": 200},
                                ),
                            }
                            print(f"[✓] Cloud Cluster ({acc['username']} -> {cf_model}) responded!")
                            self._send_openai_response(openai_resp, is_stream)
                            return
                except Exception as e:
                    print(f"[!] Cloud route {acc['username']}/{cf_model} warning: {e}")

        self._send_json(503, {"error": "All brain endpoints failed."})

    def _send_openai_response(self, openai_resp: dict, is_stream: bool):
        if not is_stream:
            self._send_json(200, openai_resp)
            return

        # Convert completion to OpenAI SSE stream format for streaming clients (like OpenHands/LiteLLM)
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

        content = openai_resp["choices"][0]["message"]["content"]
        chunk_id = openai_resp["id"]
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


def run_server(port=8080):
    server = ThreadingHTTPServer(("0.0.0.0", port), GatewayHandler)
    print(f"\n{'='*70}")
    print(f"🚀 [MOSSAD BRAIN GATEWAY v3.0] Listening on http://0.0.0.0:{port}/v1")
    print(f"🔗 Primary: Kaggle T4 GPU | Failover: 3-Account Cloud Cluster (Qwen-32B / Llama-70B)")
    print(f"{'='*70}\n")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
