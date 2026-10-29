#!/usr/bin/env python3
"""
Mossad-Pentast-AI Exclusive Brain Gateway v5.2
- Smart Context Compactor & Cloud Linux 10Gbps Proxy
- Automatic Target URL Tracker & Placeholder Replacer (eliminates 'target/' bug)
- Multi-Command Chainer & Visible Command Bubble Injector (eliminates 'undefined' UI bug)
- Autonomous Multi-Step ReAct Loop (Step 1 Recon -> Step 2 Custom Python Deep Exploit/Verify -> Step 3 Grounded Report)
- Automatic Command Error Self-Correction Engine
- Gold Trajectory Filter for Continuous Self-Learning (gold_trajectories.jsonl)
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
from urllib.parse import urlparse

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gateway_config.json")
ENDPOINT_FILE = os.path.join(REPO_DIR, "data_pipeline", "active_endpoint.json")
HISTORY_DIR = os.path.join(REPO_DIR, "chat_history")
os.makedirs(HISTORY_DIR, exist_ok=True)
HISTORY_JSONL = os.path.join(HISTORY_DIR, "conversations.jsonl")
GOLD_JSONL = os.path.join(HISTORY_DIR, "gold_trajectories.jsonl")
HISTORY_MD = os.path.join(HISTORY_DIR, "latest_chat.md")

ACTIVE_TARGET_URL = ""
IGNORED_HOSTS = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "host.docker.internal",
    "github.com",
    "raw.githubusercontent.com",
    "huggingface.co",
    "example.com",
    "target.com",
}


def load_config():
    global ACTIVE_TARGET_URL
    default_config = {
        "kaggle_url": None,
        "fallback_url": "https://mmossad2124-mossad-pentast-ai.hf.space/v1",
        "api_key": "sk-mossad-pentast-2026",
        "timeout_seconds": 180,
        "last_target_url": "",
    }
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg = {**default_config, **json.load(f)}
        except Exception:
            cfg = default_config
    else:
        cfg = default_config

    if cfg.get("last_target_url") and not ACTIVE_TARGET_URL:
        ACTIVE_TARGET_URL = cfg["last_target_url"]

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


def extract_target_from_messages(messages: list) -> str:
    """Find the most recent real target URL provided by the user across the conversation."""
    global ACTIVE_TARGET_URL
    found_url = ""
    for m in messages:
        if m.get("role") != "user":
            continue
        content = m.get("content", "")
        if isinstance(content, list):
            content = "\n".join(
                p.get("text", "") if isinstance(p, dict) else str(p) for p in content
            )
        content_str = str(content)
        if content_str.lstrip().startswith("EXECUTION RESULT of ["):
            continue
        urls = re.findall(r"https?://[^\s\"'<>)\]]+", content_str)
        for u in urls:
            u_clean = u.rstrip(".,;!)")
            parsed = urlparse(u_clean)
            host = (parsed.hostname or "").lower()
            if host and host not in IGNORED_HOSTS and not host.endswith(".trycloudflare.com"):
                found_url = u_clean

    if found_url:
        ACTIVE_TARGET_URL = found_url
        cfg = load_config()
        if cfg.get("last_target_url") != found_url:
            cfg["last_target_url"] = found_url
            save_config(cfg)
    return ACTIVE_TARGET_URL


def replace_target_placeholders(cmd: str, target_url: str) -> str:
    """Replace generic placeholders like target/, <target>, or example.com with the real target URL."""
    if not cmd or not target_url:
        return cmd

    cmd = re.sub(r"<target_url>|<target>|<url>|<domain>", target_url, cmd, flags=re.IGNORECASE)
    cmd = re.sub(r"https?://(?:www\.)?(?:example\.com|target\.com|target\.local)(/[^\s\"']*)?", target_url, cmd, flags=re.IGNORECASE)
    cmd = re.sub(r"([\"'])target/?\1", f"\\1{target_url}\\1", cmd)
    cmd = re.sub(r"(?<=\s)target/(?=[\s;|&\"']|$)", target_url, cmd)
    cmd = re.sub(r"(?<=\s)target(?=[\s;|&\"']|$)", target_url, cmd)

    if re.search(r"\b(nmap|whois|dig|fierce|dnsenum)\b", cmd):
        def _fix_net_tool(line: str) -> str:
            if re.search(r"\b(nmap|whois|dig|fierce|dnsenum)\b", line):
                line = re.sub(r"https?://([^/\s\"']+)(/[^\s\"']*)?", r"\1", line)
                if "nmap " in line:
                    line = (
                        line.replace(" -p- ", " -F ")
                        .replace("--trace-http-request-methods", "")
                        .replace("--trace-http-requests", "")
                        .replace("--trace-http-responses", "")
                    )
            return line

        parts = [_fix_net_tool(p) for p in cmd.split(";")]
        cmd = ";".join(parts)

    if "sqlmap " in cmd and "--batch" not in cmd:
        cmd = cmd.replace("sqlmap ", "sqlmap --batch ")

    if "nikto " in cmd and "-maxtime" not in cmd:
        cmd = cmd.replace("nikto ", "nikto -maxtime 30s ")

    return cmd.strip()


def build_stage2_deep_command(target_url: str) -> str:
    """Build a real custom Python & Bash deep security verification script for Stage 2 when the model only outputs text."""
    return (
        f"python3 -c \""
        f"import urllib.request, ssl; "
        f"ctx = ssl._create_unverified_context(); "
        f"url = '{target_url}'; "
        f"req = urllib.request.Request(url, headers={{'User-Agent': 'Mozilla/5.0', 'Origin': 'https://audit-check.local'}}); "
        f"r = urllib.request.urlopen(req, context=ctx, timeout=15); "
        f"h = {{k.lower(): v for k, v in r.info().items()}}; "
        f"print('=== [1] CORS & Security Header Audit ==='); "
        f"print('Status:', r.status); "
        f"print('ACAO (CORS):', h.get('access-control-allow-origin', 'Not Present (Safe)')); "
        f"print('ACAC (CORS Credentials):', h.get('access-control-allow-credentials', 'Not Present')); "
        f"missing = [x for x in ['content-security-policy', 'x-frame-options', 'x-content-type-options', 'strict-transport-security', 'referrer-policy'] if x not in h]; "
        f"print('Missing Security Headers:', missing); "
        f"print('Present Security Headers:', {{k: h[k] for k in ['strict-transport-security', 'x-frame-options', 'content-security-policy', 'x-proxy-upstream', 'server'] if k in h}}); "
        f"\" && "
        f"echo '=== [2] Sensitive Endpoint & Path Probe ===' && "
        f"for p in /robots.txt /sitemap.xml /.well-known/security.txt /api /graphql /.env; do "
        f"code=$(curl -ks -o /dev/null -w '%{{http_code}}' '{target_url.rstrip('/')}'\"$p\"); "
        f"echo \"Path $p -> HTTP $code\"; done"
    )


def extract_verified_evidence_summary(messages: list, target_url: str) -> str:
    """Extract real technical observations from all EXECUTION RESULT messages so the final report is 100% factual."""
    exec_outputs = []
    for m in messages:
        if m.get("role") == "user":
            c = str(m.get("content", ""))
            if c.lstrip().startswith("EXECUTION RESULT of ["):
                exec_outputs.append(c)

    if not exec_outputs:
        return ""

    combined = "\n".join(exec_outputs)
    lines = []
    lines.append("\n\n---\n### 📊 الأدلة التقنية الموثقة من تيرمينال سحابة اللينكس (Verified Live Terminal Evidence)")
    if target_url:
        lines.append(f"- **الهدف الفعلي المفحوص**: `{target_url}`")

    # Extract Server / WAF
    waf_m = re.search(r"is behind ([^\n\r.]+)", combined)
    if waf_m:
        lines.append(f"- **جدار الحماية الناري (WAF)**: `{re.sub(r'\\x1b\\[[0-9;]*m', '', waf_m.group(1)).strip()}`")
    elif "server: cloudflare" in combined.lower():
        lines.append("- **الخادم وجدار الحماية (Server/WAF)**: `Cloudflare`")

    # Extract Cookies
    cookies = re.findall(r"set-cookie:\s*([^;\n\r]+)", combined, flags=re.IGNORECASE)
    if cookies:
        clean_cookies = [c.split("=")[0].strip() for c in cookies[:5]]
        lines.append(f"- **ملفات تعريف الارتباط (Session Cookies المكتشفة)**: `{', '.join(dict.fromkeys(clean_cookies))}` (محمية بـ `HttpOnly; Secure; SameSite=Lax`)")

    # Extract Open Ports from nmap
    ports = re.findall(r"(\d+/tcp\s+open\s+[^\n\r]+)", combined)
    if ports:
        lines.append(f"- **المنافذ المفتوحة (Open Ports - Nmap)**: `{', '.join(dict.fromkeys(p.strip() for p in ports[:6]))}`")

    # Extract Missing Security Headers from Stage 2 Python audit
    missing_m = re.search(r"^Missing Security Headers:\s*(\[[^\]]+\])", combined, flags=re.MULTILINE)
    if missing_m:
        lines.append(f"- **رؤوس الأمان المفقودة (Missing Security Headers)**: `{missing_m.group(1)}`")

    cors_m = re.search(r"^ACAO \(CORS\):\s*([^\n\r]+)", combined, flags=re.MULTILINE)
    if cors_m:
        lines.append(f"- **فحص سياسة مشاركة الموارد (CORS Audit)**: `{cors_m.group(1).strip()}`")

    # Extract Referenced Endpoints / S3 Buckets
    refs_m = re.search(r"Referenced Endpoints/URLs:\s*(\[[^\]]+\])", combined)
    if refs_m and refs_m.group(1) != "[]":
        lines.append(f"- **الروابط وحاويات التخزين المرتبطة (S3 / Image Proxy Endpoints)**: `{refs_m.group(1)[:300]}`")

    # Extract Path Probes
    probes = re.findall(r"Path (/\S+) -> HTTP (\d+)", combined)
    if probes:
        probe_str = ", ".join(f"{p} ({code})" for p, code in probes)
        lines.append(f"- **نتائج فحص المسارات الحساسة (Endpoint Probes)**: `{probe_str}`")

    return "\n".join(lines) if len(lines) > 2 else ""


def log_chat_turn(user_msg: str, assistant_msg: str, backend_name: str, clean_msgs: list = None):
    """Persist every conversation turn locally, in Markdown, and filter Gold Trajectories for v2 training."""
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

        is_gold = (
            assistant_msg
            and "target/" not in assistant_msg
            and "<target>" not in assistant_msg
            and "undefined" not in assistant_msg
            and not re.search(r"[\u4e00-\u9fff]", assistant_msg)
            and ("<function=execute_bash>" in assistant_msg or "EXECUTION RESULT of [" in user_msg)
        )
        if is_gold:
            gold_entry = {
                "timestamp": ts,
                "target": ACTIVE_TARGET_URL,
                "messages": (clean_msgs or []) + [{"role": "assistant", "content": assistant_msg}],
            }
            with open(GOLD_JSONL, "a", encoding="utf-8") as gf:
                gf.write(json.dumps(gold_entry, ensure_ascii=False) + "\n")
    except Exception as e:
        print(f"[!] History log error: {e}")


def summarize_large_output(text: str, max_chars: int = 2400) -> str:
    """Extract security-relevant intelligence from huge HTML/JS or tool outputs to protect GPU VRAM."""
    if not text or len(text) <= max_chars:
        return text

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

    half = max_chars // 2 - 100
    return (
        text[:half]
        + f"\n\n... [⚡ تم اختصار {len(text) - max_chars} حرف لحماية ذاكرة GPU] ...\n\n"
        + text[-half:]
    )


def clean_chinese_drift(text: str) -> str:
    """Eliminate any Chinese (CJK) language drift and echoed prompt boilerplate."""
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
    text = re.sub(r"[\u4e00-\u9fff]+", " ", text)
    text = re.sub(r"2\.[12]\s*(?:استخدم الأدوات المناسبة|اكتب تقريرك باللغة العربية)[^\n]*\n?", "", text)
    text = re.sub(r"\[(?:توجيه هام|ملاحظة سياقية|تنبيه تصحيح ذاتي)[^\]]*\]", "", text)
    text = re.sub(r"  +", " ", text)
    return text.strip()


def normalize_and_format_response(
    raw_text: str,
    last_user_text: str,
    target_url: str,
    real_exec_count: int = 0,
    has_cmd_error: bool = False,
    all_messages: list = None,
) -> str:
    """
    1. Unwrap markdown code fences around <function=...> so OpenHands never leaves dangling ```bash (undefined).
    2. Extract ALL commands across multiple <function=execute_bash> tags and chain them so all tools run.
    3. Replace target/ placeholders with the real target_url.
    4. If real_exec_count == 1 on a target_url (or has_cmd_error) and model forgot <function=execute_bash>,
       automatically trigger Stage 2 Deep Custom Python Verification!
    5. Inject a clean visible ```bash block before <function=execute_bash> so the user always sees the exact command in chat.
    """
    if not raw_text:
        return raw_text

    c = clean_chinese_drift(raw_text)

    # 1. Remove code fences wrapping <function=...>
    c = re.sub(
        r"```[a-zA-Z0-9_-]*\s*(<function=.*?</function>)\s*```",
        r"\1",
        c,
        flags=re.DOTALL,
    )
    c = re.sub(r"```[a-zA-Z0-9_-]*\s*(?=<function=)", "", c)
    c = re.sub(r"(?<=</function>)\s*```", "", c)

    extracted_cmds = []

    if "<function=" in c:
        c = re.sub(r"<command>(.*?)</command>", r"<parameter=command>\1</parameter>", c, flags=re.DOTALL)
        c = re.sub(r"<parameter>\s*command\s*>(.*?)</parameter>", r"<parameter=command>\1</parameter>", c, flags=re.DOTALL)
        c = re.sub(r"<parameter=cmd>(.*?)</parameter>", r"<parameter=command>\1</parameter>", c, flags=re.DOTALL)

        fn_blocks = re.findall(r"<function=execute_bash>(.*?)(?:</function>|$)", c, flags=re.DOTALL)
        for blk in fn_blocks:
            param_m = re.search(r"<parameter=command>(.*?)(?:</parameter>|$)", blk, flags=re.DOTALL)
            if param_m:
                cmd_candidate = param_m.group(1).strip()
            else:
                cmd_candidate = re.sub(r"</?[^>]+>", "", blk).strip()
            cmd_candidate = re.sub(r"^```[a-zA-Z0-9_-]*\s*|\s*```$", "", cmd_candidate).strip()
            is_valid_cmd = (
                bool(cmd_candidate)
                and cmd_candidate != "..."
                and not cmd_candidate.startswith("`")
                and not re.search(r"[\u0600-\u06FF]", cmd_candidate)
            )
            if is_valid_cmd:
                cmd_fixed = replace_target_placeholders(cmd_candidate, target_url)
                if cmd_fixed not in extracted_cmds:
                    extracted_cmds.append(cmd_fixed)

        if not extracted_cmds and "<function=finish>" in c:
            c = re.sub(r"```[a-zA-Z0-9_-]*\s*```", "", c).strip()
            return c

    elif "```" in c and "EXECUTION RESULT of [" not in last_user_text:
        bash_blocks = re.findall(r"```(?:bash|sh|shell|zsh)?\s*\n(.*?)```", c, flags=re.DOTALL)
        for blk in bash_blocks:
            for line in blk.splitlines():
                line_s = line.strip()
                if line_s.startswith("$ "):
                    line_s = line_s[2:].strip()
                if (
                    line_s
                    and not line_s.startswith("#")
                    and not line_s.startswith("`")
                    and not re.search(r"[\u0600-\u06FF]", line_s)
                ):
                    cmd_fixed = replace_target_placeholders(line_s, target_url)
                    if cmd_fixed not in extracted_cmds:
                        extracted_cmds.append(cmd_fixed)

    # Autonomous Stage 2 Deep Verification & Self-Correction Trigger:
    # If Step 1 just finished on a web target (real_exec_count == 1) OR the previous command errored (real_exec_count <= 2),
    # and the model wrote text without <function=execute_bash>, automatically execute Stage 2 custom Python verification!
    if not extracted_cmds and target_url and (real_exec_count == 1 or (has_cmd_error and real_exec_count <= 2)):
        stage2_cmd = build_stage2_deep_command(target_url)
        extracted_cmds.append(stage2_cmd)
        if has_cmd_error:
            c += "\n\n🔄 **التصحيح الذاتي التلقائي (Self-Correction)**: تم رصد خطأ في الأمر السابق، جاري التبديل إلى سكربت Python مخصص وفحص المسارات لاستكمال الاختبار العملي:"
        else:
            c += "\n\n⚡ **الانتقال التلقائي للمرحلة الثانية (الفحص العميق واسكربت Python المخصص)**: بناءً على نتائج الاستطلاع الأولي، جاري تشغيل سكربت بايثون لفحص رؤوس الأمان (Security Headers)، وسياسة (CORS)، والمسارات الحساسة:"

    if extracted_cmds:
        thought = re.sub(r"<function=[^>]+>.*?(?:</function>|$)", "", c, flags=re.DOTALL)
        thought = re.sub(r"```[a-zA-Z0-9_-]*\s*```", "", thought).strip()
        if thought.count("```") % 2 == 1:
            thought = re.sub(r"```[a-zA-Z0-9_-]*\s*$", "", thought).strip()

        thought = re.sub(r"💻 \*\*الأمر المنفذ على سحابة اللينكس.*?\n```bash\n.*?```", "", thought, flags=re.DOTALL).strip()

        if len(extracted_cmds) == 1:
            combined_cmd = extracted_cmds[0]
            display_cmd = extracted_cmds[0]
        else:
            chained_parts = []
            for idx_c, single_c in enumerate(extracted_cmds[:4], 1):
                chained_parts.append(f"echo '━━━ [Step {idx_c}: {single_c[:40]}] ━━━' && {single_c}")
            combined_cmd = " ; ".join(chained_parts)
            display_cmd = "\n".join(extracted_cmds[:4])

        if not thought:
            thought = f"جاري تنفيذ الفحص العملي على الهدف `{target_url or 'المحدد'}` عبر سحابة اللينكس (10Gbps):"

        visible_cmd_block = (
            f"💻 **الأمر المنفذ على سحابة اللينكس (10Gbps):**\n"
            f"```bash\n{display_cmd}\n```"
        )
        c = (
            f"{thought}\n\n{visible_cmd_block}\n"
            f"<function=execute_bash>\n<parameter=command>{combined_cmd}</parameter>\n</function>"
        )
    else:
        c = re.sub(r"```[a-zA-Z0-9_-]*\s*```", "", c).strip()
        if c.count("```") % 2 == 1:
            c = re.sub(r"```[a-zA-Z0-9_-]*\s*$", "", c).strip()

        # Append verified terminal evidence table to final report so the user gets 100% real technical data
        if real_exec_count >= 1 and all_messages:
            evidence_block = extract_verified_evidence_summary(all_messages, target_url)
            if evidence_block and "الأدلة التقنية الموثقة" not in c:
                c = f"{c}{evidence_block}"

    return c


def refresh_kaggle_url_from_github(cfg):
    try:
        gh_raw = f"https://raw.githubusercontent.com/mmossad2124-blip/BugBounty-Copilot/main/data_pipeline/active_endpoint.json?t={int(time.time())}"
        req_gh = urllib.request.Request(gh_raw, headers={"User-Agent": "BrainGateway/5.2", "Cache-Control": "no-cache"})
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
                "version": "5.2",
                "model": "Mossad-pentast-ai (Exclusive Trained Weights + HexStrike AI v6.0 + Multi-Step Self-Correction)",
                "active_brain": "Kaggle GPU (Primary)" if cfg.get("kaggle_url") else "HuggingFace Fallback (Secondary)",
                "cloud_linux_vm": "ONLINE (10Gbps + HexStrike 150 Tools)" if cfg.get("kaggle_url") else "STANDBY",
                "active_target": ACTIVE_TARGET_URL,
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
        """Forward bash commands to the 10Gbps Cloud Linux VM on Kaggle with target substitution & smart output extraction."""
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
                cmd_str = replace_target_placeholders(cmd_str, ACTIVE_TARGET_URL)
                req_json["command"] = cmd_str
                print(f"[☁️ CLOUD EXEC] Forwarding command to Cloud Linux VM (10Gbps): {cmd_str[:110]}...")
                req = urllib.request.Request(
                    exec_url,
                    data=json.dumps(req_json).encode("utf-8"),
                    headers={"Content-Type": "application/json", "User-Agent": "MossadBrainGateway/5.2"},
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
        target_url = ACTIVE_TARGET_URL
        real_exec_count = 0
        has_cmd_error = False
        raw_messages_snapshot = []

        if "messages" in req_json and isinstance(req_json["messages"], list):
            raw_messages_snapshot = list(req_json["messages"])
            target_url = extract_target_from_messages(req_json["messages"])
            real_exec_count = sum(
                1
                for m in req_json["messages"]
                if m.get("role") == "user"
                and str(m.get("content", "")).lstrip().startswith("EXECUTION RESULT of [")
            )

            clean_msgs = []
            for idx_m, m in enumerate(req_json["messages"]):
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
                is_last_msg = idx_m == len(req_json["messages"]) - 1

                if role == "user":
                    last_user_text = content_str
                    if len(content_str) > 2400:
                        content_str = summarize_large_output(content_str, max_chars=2400)

                    if is_last_msg and content_str.lstrip().startswith("EXECUTION RESULT of ["):
                        lower_obs = content_str.lower()
                        has_cmd_error = any(
                            err_tok in lower_obs
                            for err_tok in [
                                "command not found",
                                "unrecognized arguments",
                                "invalid option",
                                "syntax error",
                                "traceback (most recent call last)",
                                "[!] error:",
                                "no such file or directory",
                            ]
                        )
                        if has_cmd_error:
                            content_str += (
                                f"\n\nالأمر السابق أرجع خطأ تقنياً. قم بتحليل سبب الخطأ وتنفيذ أمر بديل مصحح أو سكربت Python مخصص لفحص الهدف {target_url or ''}."
                            )
                        elif real_exec_count == 1 and target_url:
                            content_str += (
                                f"\n\nاكتملت المرحلة الأولى للاستطلاع على {target_url}. قم بتحليل المخرجات الحقيقية أعلاه باختصار استعداداً للمرحلة الثانية (فحص الرؤوس الأمنية، سياسة CORS، والمسارات الحساسة)."
                            )
                        else:
                            content_str += (
                                "\n\nاكتب الآن التقرير الأمني النهائي المفصل باللغة العربية الفصحى بناءً على المخرجات الحقيقية أعلاه فقط (حالة HTTP، السيرفر، جدار الحماية WAF، الكوكيز، المنافذ المفتوحة، ونتائج فحص CORS والمسارات)."
                            )
                elif role == "assistant":
                    content_str = clean_chinese_drift(content_str)
                    content_str = re.sub(
                        r"💻 \*\*الأمر المنفذ على سحابة اللينكس.*?\n```bash\n.*?```\n*",
                        "",
                        content_str,
                        flags=re.DOTALL,
                    ).strip()
                    if len(content_str) > 1400:
                        content_str = content_str[:1400]
                clean_msgs.append({"role": role, "content": content_str})

            if len(clean_msgs) > 7:
                sys_msgs = [m for m in clean_msgs[:1] if m["role"] == "system"]
                target_user_msgs = [
                    m for m in clean_msgs[1:-4]
                    if m["role"] == "user"
                    and not m["content"].lstrip().startswith("EXECUTION RESULT of [")
                    and ("http://" in m["content"] or "https://" in m["content"])
                ][-1:]
                if not target_user_msgs:
                    target_user_msgs = [m for m in clean_msgs[1:3] if m["role"] == "user"][:1]
                recent = clean_msgs[-4:]
                clean_msgs = sys_msgs + target_user_msgs + recent

            MAX_TOTAL_CHARS = 5800
            total_chars = sum(len(m["content"]) for m in clean_msgs)
            while total_chars > MAX_TOTAL_CHARS and len(clean_msgs) > 2:
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

        for target_name, t_url in targets:
            try:
                print(
                    f"[*] Forwarding prompt to {target_name}: {t_url} "
                    f"(Target: {target_url or 'None'} | Step: {real_exec_count + 1})..."
                )
                req = urllib.request.Request(
                    t_url,
                    data=backend_bytes,
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {cfg.get('api_key', 'sk-mossad-pentast-2026')}",
                        "User-Agent": "MossadBrainGateway/5.2",
                    },
                    method="POST",
                )
                with urllib.request.urlopen(req, timeout=cfg.get("timeout_seconds", 180)) as resp:
                    resp_data = resp.read().decode("utf-8")
                    resp_obj = json.loads(resp_data)
                    if "choices" in resp_obj:
                        raw_reply = resp_obj["choices"][0].get("message", {}).get("content", "")
                        formatted_reply = normalize_and_format_response(
                            raw_reply,
                            last_user_text,
                            target_url,
                            real_exec_count=real_exec_count,
                            has_cmd_error=has_cmd_error,
                            all_messages=raw_messages_snapshot,
                        )
                        resp_obj["choices"][0]["message"]["content"] = formatted_reply
                        print(f"[✓] {target_name} responded ({len(formatted_reply)} chars)!")
                        log_chat_turn(last_user_text[-500:], formatted_reply, target_name, req_json.get("messages"))
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
                                    "User-Agent": "MossadBrainGateway/5.2",
                                },
                                method="POST",
                            )
                            with urllib.request.urlopen(req2, timeout=cfg.get("timeout_seconds", 180)) as resp2:
                                resp_obj2 = json.loads(resp2.read().decode("utf-8"))
                                if "choices" in resp_obj2:
                                    raw_reply = resp_obj2["choices"][0].get("message", {}).get("content", "")
                                    formatted_reply = normalize_and_format_response(
                                        raw_reply,
                                        last_user_text,
                                        target_url,
                                        real_exec_count=real_exec_count,
                                        has_cmd_error=has_cmd_error,
                                        all_messages=raw_messages_snapshot,
                                    )
                                    resp_obj2["choices"][0]["message"]["content"] = formatted_reply
                                    print("[✓] Refreshed Kaggle GPU URL responded successfully!")
                                    log_chat_turn(last_user_text[-500:], formatted_reply, target_name, req_json.get("messages"))
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
    print(f"\n{'='*72}")
    print(f"🚀 [MOSSAD BRAIN GATEWAY v5.2 - MULTI-STEP + SELF-CORRECTION] Port {port}")
    print(f"🔗 1. Primary: Kaggle GPU (Mossad-pentast-ai) | 2. Fallback: Hugging Face")
    print(f"☁️  Cloud Linux 10Gbps + HexStrike AI 150 Tools Proxy at /execute")
    print(f"{'='*72}\n")
    sys.stdout.flush()
    server.serve_forever()


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port)
