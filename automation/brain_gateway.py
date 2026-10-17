#!/usr/bin/env python3
"""
Mossad-Pentast-AI Exclusive Brain Gateway, Smart Context Compactor & Cloud Linux Proxy
Listens on http://0.0.0.0:8080/v1 (accessible by Host, Docker OpenHands, and CLI)
STRICT POLICY: ONLY routes to our own fine-tuned model (Mossad-pentast-ai).
Never uses external/third-party models.

Enhancements v4.0:
  1. Smart HTML/JS & Tool Observation Compactor (prevents 30KB curl dumps from causing CUDA OOM HTTP 500 on T4 GPU)
  2. HexStrike AI v6.0 (150+ Tools) + Custom Scripting integration on 10Gbps Cloud Linux VM
  3. Zero-Chinese Guard (prevents Qwen base-model CJK language drift on English terminal errors)
  4. Automatic XML/Bash tool call normalization (<command> / ```bash -> <parameter=command>)
"""

import json
import os
import re
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


def summarize_large_output(text: str, max_chars: int = 2400) -> str:
    """Extract security-relevant intelligence from huge HTML/JS or tool outputs to protect GPU VRAM."""
    if not text or len(text) <= max_chars:
        return text

    # Check if it looks like raw HTML/JS from curl
    lower = text.lower()
    if "<html" in lower or "<!doctype" in lower or "<script" in lower or "document.getelementbyid" in lower:
        titles = re.findall(r"<title[^>]*>(.*?)</title>", text, flags=re.IGNORECASE | re.DOTALL)
        forms = re.findall(r"<form[^>]*>.*?</form>", text, flags=re.IGNORECASE | re.DOTALL)
        inputs = re.findall(r"<input[^>]*>", text, flags=re.IGNORECASE)
        scripts = re.findall(r"<script[^>]+src=[\"']([^\"']+)[\"']", text, flags=re.IGNORECASE)
        links = re.findall(r"href=[\"']([^\"']+)[\"']", text, flags=re.IGNORECASE)
        apis = re.findall(r"https?://[^\s\"'<>]+|/api/[^\s\"'<>]+", text)

        summary_parts = [
            f"[⚡ Smart Security Extractor: تم تلخيص صفحة الويب (الحجم الأصلي {len(text)} حرف) لحماية ذاكرة GPU واستخراج الزبدة الأمنية]:",
            f"- عنوان الصفحة (Title): {titles[0].strip() if titles else 'N/A'}",
            f"- النماذج (Forms المكتشفة: {len(forms)}): {forms[:3]}",
            f"- حقول الإدخال (Inputs المكتشفة: {len(inputs)}): {inputs[:10]}",
            f"- ملفات السكربت (Scripts المكتشفة: {len(scripts)}): {scripts[:10]}",
            f"- الروابط والمسارات (Links/Endpoints): {list(dict.fromkeys(links + apis))[:20]}",
            f"- مقتطف من بداية الاستجابة:\n{text[:700]}",
        ]
        res = "\n".join(summary_parts)
        return res[:max_chars]

    # General large command output truncation
    half = max_chars // 2 - 100
    return (
        text[:half]
        + f"\n\n... [⚡ تم اختصار {len(text) - max_chars} حرف لحماية ذاكرة GPU] ...\n\n"
        + text[-half:]
    )


def clean_chinese_drift(text: str) -> str:
    """Eliminate any Chinese (CJK) language drift while preserving Arabic/English technical content."""
    if not text:
        return text
    replacements = {
        "看来": "يبدو أن ",
        "看起来": "يبدو أن ",
        "不支持": " لا يدعم ",
        "选项": " الخيار ",
        "让我们尝试另一种方法来格式化输出": "لنجرب طريقة أخرى لتنسيق المخرجات",
        "请求响应不是有效的": "استجابة الطلب ليست بصيغة صالحة ",
        "让我们改用": "سأنتقل لاستخدام ",
        "来分析页面": " لتحليل الصفحة",
        "服务器上没有安装": "الأداة غير مثبتة، سأقوم بتثبيتها أو استخدام بديل ",
        "来获取一些基本信息": " لجلب المعلومات الأساسية",
        "：": ":",
        "。": ". ",
        "，": "، ",
    }
    for k, v in replacements.items():
        text = text.replace(k, v)
    # Remove any remaining CJK characters
    text = re.sub(r"[\u4e00-\u9fff]+", " ", text)
    text = re.sub(r"  +", " ", text)
    return text.strip()


def refresh_kaggle_url_from_github(cfg):
    try:
        gh_raw = f"https://raw.githubusercontent.com/mmossad2124-blip/BugBounty-Copilot/main/data_pipeline/active_endpoint.json?t={int(time.time())}"
        req_gh = urllib.request.Request(gh_raw, headers={"User-Agent": "BrainGateway/4.0", "Cache-Control": "no-cache"})
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
                "model": "Mossad-pentast-ai (Exclusive Trained Weights + HexStrike AI v6.0)",
                "active_brain": "Kaggle GPU (Primary)" if cfg.get("kaggle_url") else "HuggingFace Fallback (Secondary)",
                "cloud_linux_vm": "ONLINE (10Gbps + HexStrike 150 Tools)" if cfg.get("kaggle_url") else "STANDBY",
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
        """Forward bash commands to the 10Gbps Cloud Linux VM on Kaggle with smart output extraction."""
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
                if "nmap " in cmd_str:
                    cmd_str = re.sub(r"https?://([^/\s\"']+)(/[^\s\"']*)?", r"\1", cmd_str)
                    cmd_str = (
                        cmd_str.replace(" -p- ", " -F ")
                        .replace("--trace-http-request-methods", "")
                        .replace("--trace-http-requests", "")
                        .replace("--trace-http-responses", "")
                    )
                    req_json["command"] = cmd_str
                print(f"[☁️ CLOUD EXEC] Forwarding command to Cloud Linux VM (10Gbps): {cmd_str[:90]}...")
                req = urllib.request.Request(
                    exec_url,
                    data=json.dumps(req_json).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "MossadBrainGateway/4.0"},
                    method="POST",
                )
                timeout_s = int(req_json.get("timeout", 120)) + 15
                with urllib.request.urlopen(req, timeout=timeout_s) as resp:
                    resp_obj = json.loads(resp.read().decode("utf-8"))
                    if "stdout" in resp_obj and isinstance(resp_obj["stdout"], str):
                        resp_obj["stdout"] = summarize_large_output(resp_obj["stdout"], max_chars=2600)
                    if "stderr" in resp_obj and isinstance(resp_obj["stderr"], str):
                        resp_obj["stderr"] = summarize_large_output(resp_obj["stderr"], max_chars=1200)
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

        # Flatten and compact messages to prevent GPU OOM and Chinese drift
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
                    # Summarize huge tool outputs before sending to GPU
                    if len(content_str) > 2400:
                        content_str = summarize_large_output(content_str, max_chars=2400)
                    if "EXECUTION RESULT of [" in content_str:
                        content_str += (
                            "\n\n[توجيه هام لـ Mossad-pentast-ai: حلل النتيجة أعلاه باللغة العربية الفصحى فقط. "
                            "لديك 150+ أداة عبر `hexstrike` (مثل `hexstrike analyze <target>` أو `hexstrike smart-scan <target>`) "
                            "وأدوات اللينكس (`whatweb`, `wafw00f`, `nmap`, `gobuster`, `ffuf`, `sqlmap`, `nikto`, `curl`, `python3`). "
                            "إذا احتجت خطوة فحص إضافية نفذها بـ `<function=execute_bash><parameter=command>...</parameter></function>`، "
                            "وإذا اكتملت لديك النتائج اكتب تقريراً أمنياً مفصلاً باللغة العربية بدون أي وسم `<function=...>`]."
                        )
                elif role == "assistant":
                    content_str = clean_chinese_drift(content_str)
                    if len(content_str) > 1500:
                        content_str = content_str[:1500]
                clean_msgs.append({"role": role, "content": content_str})

            # Sliding context window + strict 6000-char budget so token count NEVER exceeds Unsloth max_seq_length=4096
            if len(clean_msgs) > 7:
                sys_msgs = [m for m in clean_msgs[:1] if m["role"] == "system"]
                first_user = [m for m in clean_msgs[:3] if m["role"] == "user"][:1]
                recent = clean_msgs[-4:]
                clean_msgs = sys_msgs + first_user + recent

            MAX_TOTAL_CHARS = 5800
            total_chars = sum(len(m["content"]) for m in clean_msgs)
            while total_chars > MAX_TOTAL_CHARS and len(clean_msgs) > 2:
                # Drop oldest middle message or truncate largest message
                if len(clean_msgs) > 3:
                    clean_msgs.pop(1)
                else:
                    for m in clean_msgs:
                        if len(m["content"]) > 1800:
                            m["content"] = summarize_large_output(m["content"], max_chars=1600)
                    break
                total_chars = sum(len(m["content"]) for m in clean_msgs)

            req_json["messages"] = clean_msgs

        backend_req = dict(req_json)
        backend_req["stream"] = False
        backend_req["max_tokens"] = min(int(backend_req.get("max_tokens", 512) or 512), 512)
        backend_bytes = json.dumps(backend_req).encode("utf-8")

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
                        "User-Agent": "MossadBrainGateway/4.0",
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
                        self._send_openai_response(resp_obj, is_stream, last_user_text)
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
                                    "User-Agent": "MossadBrainGateway/4.0",
                                },
                                method="POST",
                            )
                            with urllib.request.urlopen(req2, timeout=cfg.get("timeout_seconds", 180)) as resp2:
                                resp_obj2 = json.loads(resp2.read().decode("utf-8"))
                                if "choices" in resp_obj2:
                                    reply_text = resp_obj2["choices"][0].get("message", {}).get("content", "")
                                    print("[✓] Refreshed Kaggle GPU URL responded successfully!")
                                    log_chat_turn(last_user_text[-500:], reply_text, target_name)
                                    self._send_openai_response(resp_obj2, is_stream, last_user_text)
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

    def _send_openai_response(self, openai_resp: dict, is_stream: bool, last_user_text: str = ""):
        try:
            c = openai_resp["choices"][0]["message"].get("content", "")
            if c:
                c = clean_chinese_drift(c)
                if "<function=" in c:
                    c = re.sub(r"<command>(.*?)</command>", r"<parameter=command>\1</parameter>", c, flags=re.DOTALL)
                    c = re.sub(r"<parameter>\s*command\s*>(.*?)</parameter>", r"<parameter=command>\1</parameter>", c, flags=re.DOTALL)
                    c = re.sub(r"<parameter=cmd>(.*?)</parameter>", r"<parameter=command>\1</parameter>", c, flags=re.DOTALL)
                    if "<function=execute_bash>" in c and "<parameter=command>" not in c:
                        def _wrap_raw_bash(m):
                            inner = re.sub(r"</?[^>]+>", "", m.group(1)).strip()
                            return f"<function=execute_bash>\n<parameter=command>{inner}</parameter>\n</function>"
                        c = re.sub(r"<function=execute_bash>(.*?)(?:</function>|$)", _wrap_raw_bash, c, flags=re.DOTALL)
                elif "```" in c and "EXECUTION RESULT of [" not in last_user_text:
                    bash_blocks = re.findall(r"```(?:bash|sh|shell|zsh)?\s*\n(.*?)```", c, flags=re.DOTALL)
                    cmds = []
                    for blk in bash_blocks:
                        for line in blk.splitlines():
                            line_s = line.strip()
                            if line_s and not line_s.startswith("#"):
                                cmds.append(line_s)
                    if cmds:
                        combined_cmd = " && ".join(cmds[:3])
                        thought_text = re.sub(r"```(?:bash|sh|shell|zsh)?\s*\n.*?```", "", c, flags=re.DOTALL).strip()
                        c = f"{thought_text}\n<function=execute_bash>\n<parameter=command>{combined_cmd}</parameter>\n</function>"
                openai_resp["choices"][0]["message"]["content"] = c
        except Exception as e:
            print(f"[!] Normalization warning: {e}")

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
    print(f"🚀 [MOSSAD BRAIN GATEWAY v4.0 - HEXSTRIKE + EXCLUSIVE MODEL] Port {port}")
    print(f"🔗 1. Primary: Kaggle GPU (Mossad-pentast-ai) | 2. Fallback: Hugging Face")
    print(f"☁️  Cloud Linux 10Gbps + HexStrike AI 150 Tools Proxy at /execute")
    print(f"{'='*70}\n")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
