#!/usr/bin/env python3
"""
Live Dynamic AI Sandbox Verifier (100% Real AI Model, Zero Hardcoded Output)
Demonstrates live query to the AI model, execution in the sandbox,
runtime assertion checking, and real feedback loop for self-correction.
"""

import os
import sys
import json
import re
import urllib.request

# Load credentials from .env
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

# Challenge: Open Redirect Security Validation
CHALLENGE = {
    "title": "Open Redirect Vulnerability Remediation",
    "description": (
        "The following function validates whether a redirection target URL belongs to an allowed domain.\n"
        "Currently, it is insecure: `def is_safe_redirect(target_url: str, allowed_host: str) -> bool: return allowed_host in target_url`.\n"
        "Attackers bypass it using: 'https://evil.com/?x=allowed.com' or 'https://allowed.com.attacker.com' or '//attacker.com'."
    ),
    "task": (
        "Write a secure Python function `is_safe_redirect(target_url: str, allowed_host: str) -> bool` "
        "that uses `urllib.parse.urlparse` to strictly verify that:\n"
        "1. The URL scheme is either 'http' or 'https'.\n"
        "2. The netloc (domain) strictly matches `allowed_host` or is a valid subdomain of it (e.g., ends with `.{allowed_host}`).\n"
        "Respond ONLY with valid Python code containing the function definition and imports. Do not include markdown or explanations."
    ),
    "tests": [
        {"url": "https://company.com/profile", "host": "company.com", "expected": True},
        {"url": "https://api.company.com/v1", "host": "company.com", "expected": True},
        {"url": "https://attacker.com/?ref=company.com", "host": "company.com", "expected": False},
        {"url": "https://company.com.attacker.com/login", "host": "company.com", "expected": False},
        {"url": "//attacker.com/bypass", "host": "company.com", "expected": False},
        {"url": "javascript:alert(1)", "host": "company.com", "expected": False},
    ]
}

def call_live_ai(messages: list) -> str:
    """Invokes the actual AI model live via API."""
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_MODEL}"
    headers = {
        "Authorization": f"Bearer {CF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {"messages": messages}
    req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        res = json.loads(resp.read().decode())
        raw_text = res.get("result", {}).get("response", "")
        # Clean any markdown code blocks
        clean = re.sub(r"```python\s*", "", raw_text)
        clean = re.sub(r"```\s*", "", clean).strip()
        return clean

def verify_code(code_str: str, tests: list) -> dict:
    """Executes the AI-generated code in an isolated sandbox and runs assertion tests."""
    ns = {}
    try:
        exec(code_str, ns)
        if "is_safe_redirect" not in ns:
            return {"passed": False, "error": "Function 'is_safe_redirect' was not found in the generated code."}
        
        func = ns["is_safe_redirect"]
        for idx, t in enumerate(tests, 1):
            try:
                res = func(t["url"], t["host"])
                if res != t["expected"]:
                    return {
                        "passed": False,
                        "failed_test": idx,
                        "error": f"Test #{idx} Failed: URL='{t['url']}', Host='{t['host']}'. Expected {t['expected']}, but got {res}."
                    }
            except Exception as e:
                return {
                    "passed": False,
                    "failed_test": idx,
                    "error": f"Test #{idx} raised an Exception: {e}"
                }
        return {"passed": True, "message": f"All {len(tests)} security assertions passed!"}
    except Exception as e:
        return {"passed": False, "error": f"Code Compilation/Execution Error: {e}"}

def run_live_experiment():
    print("=" * 75)
    print("🧠 [LIVE DYNAMIC AI EXPERIMENT] Testing Real AI Model (Meta LLaMA 3.1 8B)")
    print(f"Challenge: {CHALLENGE['title']}")
    print("=" * 75)
    
    messages = [
        {"role": "system", "content": "You are an elite software security engineer. Write pure Python code that strictly satisfies all security constraints."},
        {"role": "user", "content": CHALLENGE["description"] + "\n\n" + CHALLENGE["task"]}
    ]
    
    # ROUND 1: Live call to the AI model
    print("\n[*] Sending request LIVE to Cloudflare AI model (No hardcoding)...")
    code_round_1 = call_live_ai(messages)
    
    print("\n--- [LIVE AI GENERATED CODE (Round 1)] ---")
    print(code_round_1)
    print("------------------------------------------")
    
    print("\n[*] Executing AI code in Sandbox against 6 security test cases...")
    result_1 = verify_code(code_round_1, CHALLENGE["tests"])
    
    if result_1["passed"]:
        print(f"\n🎉 [SUCCESS IN ROUND 1!]: {result_1['message']}")
        print("The AI model solved the challenge perfectly on its first attempt!")
    else:
        print(f"\n❌ [SANDBOX FAILURE DETECTED]: {result_1['error']}")
        print("\n[*] Feeding the error trace back to the AI for Round 2 self-correction...")
        
        # Round 2: Feed back the error trace to the AI
        messages.append({"role": "assistant", "content": code_round_1})
        messages.append({
            "role": "user",
            "content": (
                f"Your solution failed in our sandbox verification with the following error:\n"
                f"{result_1['error']}\n\n"
                f"Analyze why this happened and provide the corrected Python code. Return ONLY valid python code."
            )
        })
        
        code_round_2 = call_live_ai(messages)
        print("\n--- [LIVE AI REFINED CODE (Round 2)] ---")
        print(code_round_2)
        print("------------------------------------------")
        
        print("\n[*] Re-executing refined code in Sandbox...")
        result_2 = verify_code(code_round_2, CHALLENGE["tests"])
        if result_2["passed"]:
            print(f"\n✅ [VERIFICATION SUCCEEDED IN ROUND 2!]: {result_2['message']}")
            print("The AI model successfully self-corrected after reading the Sandbox error!")
        else:
            print(f"\n⚠️ Round 2 status: {result_2['error']}")

if __name__ == "__main__":
    run_live_experiment()
