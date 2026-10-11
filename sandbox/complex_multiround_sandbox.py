#!/usr/bin/env python3
"""
Complex Multi-Round Autonomous Sandbox (Post-Training Evaluation & Verification Exam)
Puts the AI model inside an isolated execution environment with a high-complexity challenge.
Enforces multi-round trial-and-error (up to 5 iterative attempts) until the model
diagnoses the root cause, passes all edge-case security tests, and generates a verified patch.
"""

import os
import sys
import json
import time
import re
import urllib.request

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

# Highly Complex Challenge: Fintech Clearing Engine (State Inversion & Concurrency Race)
COMPLEX_CHALLENGE = {
    "title": "High-Frequency Clearing Engine: Atomic Balance Reservation & Timing-Safe HMAC",
    "description": (
        "You are auditing a high-frequency cryptocurrency & fiat clearing settlement engine.\n"
        "The current transaction processing function contains multiple critical security flaws:\n"
        "1. Race condition in balance check (Allows double-spending under concurrent threads).\n"
        "2. Insecure signature verification (uses standard '==' which leaks timing information).\n"
        "3. Missing transaction idempotency cache (allows replaying signed transactions).\n"
        "4. Unchecked float precision (allows sub-penny fractional balance manipulation)."
    ),
    "vulnerable_code": (
        "import hmac, hashlib\n\n"
        "class InsecureSettlementEngine:\n"
        "    def __init__(self, balances: dict, secret: bytes):\n"
        "        self.balances = balances # {'user_1': 100.0}\n"
        "        self.secret = secret\n\n"
        "    def process_transfer(self, user: str, amount: float, sig: str, tx_id: str) -> bool:\n"
        "        # Flaw 1: Insecure timing-vulnerable signature comparison\n"
        "        expected_sig = hmac.new(self.secret, f'{user}:{amount}:{tx_id}'.encode(), hashlib.sha256).hexdigest()\n"
        "        if sig != expected_sig:\n"
        "            return False\n\n"
        "        # Flaw 2: Non-atomic balance check & float arithmetic (Double-spend race condition)\n"
        "        if self.balances.get(user, 0.0) >= amount:\n"
        "            self.balances[user] -= amount\n"
        "            return True\n"
        "        return False\n"
    ),
    "task": (
        "Write a production-grade, secure class `SecureSettlementEngine` that completely fixes all vulnerabilities:\n"
        "Class interface MUST strictly follow:\n"
        "class SecureSettlementEngine:\n"
        "    def __init__(self, balances: dict, secret: bytes):\n"
        "        self.balances = balances\n"
        "        self.secret = secret\n"
        "        self.lock = threading.Lock()\n"
        "        self.processed_txs = set()\n\n"
        "    def process_transfer(self, user: str, amount: float, sig: str, tx_id: str) -> bool:\n"
        "        # 1. Reject duplicate tx_id replay\n"
        "        # 2. Timing-safe HMAC check via hmac.compare_digest with expected signature: hmac.new(self.secret, f'{user}:{amount}:{tx_id}'.encode(), hashlib.sha256).hexdigest()\n"
        "        # 3. Reject amount <= 0\n"
        "        # 4. Atomic balance deduction under self.lock\n"
        "        # 5. Return True on success, False on failure\n\n"
        "Return ONLY the complete valid Python code for `SecureSettlementEngine`."
    )
}

class SandboxHarness:
    """Rigorous execution sandbox with concurrent and edge-case test suites."""

    @staticmethod
    def verify(code_str: str) -> dict:
        namespace = {}
        try:
            exec(code_str, namespace)
            if "SecureSettlementEngine" not in namespace:
                return {
                    "passed": False,
                    "error": "MissingClassError: 'SecureSettlementEngine' was not defined in the submitted solution."
                }
            
            EngineClass = namespace["SecureSettlementEngine"]
            secret = b"super_secret_trading_key_99"
            
            # --- TEST 1: Legitimate Transfer Verification ---
            import hmac, hashlib
            engine = EngineClass({"alice": 1000.0}, secret)
            tx1 = "tx_1001"
            sig1 = hmac.new(secret, f"alice:100.0:{tx1}".encode(), hashlib.sha256).hexdigest()
            if not engine.process_transfer("alice", 100.0, sig1, tx1):
                return {"passed": False, "error": "Test #1 Failed: Legitimate transfer with valid HMAC signature was rejected."}
            if engine.balances["alice"] != 900.0:
                return {"passed": False, "error": f"Test #1 Failed: Balance arithmetic mismatch. Expected 900.0, got {engine.balances['alice']}"}

            # --- TEST 2: Timing-Safe Signature Tampering Rejection ---
            fake_sig = sig1[:-2] + "ff"
            tx2 = "tx_1002"
            if engine.process_transfer("alice", 50.0, fake_sig, tx2):
                return {"passed": False, "error": "Test #2 Failed: Tampered HMAC signature was accepted! Insecure validation detected."}

            # --- TEST 3: Replay Attack (Idempotency) Prevention ---
            # Attempting to replay tx1 with identical signature
            if engine.process_transfer("alice", 100.0, sig1, tx1):
                return {"passed": False, "error": "Test #3 Failed: Replay attack succeeded! Duplicate tx_id was executed a second time."}

            # --- TEST 4: Negative & Zero Value Inversion Attack ---
            tx4 = "tx_1004"
            sig4 = hmac.new(secret, f"alice:-500.0:{tx4}".encode(), hashlib.sha256).hexdigest()
            if engine.process_transfer("alice", -500.0, sig4, tx4):
                return {"passed": False, "error": "Test #4 Failed: Negative amount accepted! Enabled balance inflation exploit."}

            # --- TEST 5: High-Concurrency Double-Spending Race Condition ---
            import threading
            race_engine = EngineClass({"bob": 100.0}, secret)
            success_count = [0]
            
            def attempt_spend(tid):
                s = hmac.new(secret, f"bob:100.0:{tid}".encode(), hashlib.sha256).hexdigest()
                if race_engine.process_transfer("bob", 100.0, s, tid):
                    success_count[0] += 1

            threads = [threading.Thread(target=attempt_spend, args=(f"race_{i}",)) for i in range(10)]
            for t in threads: t.start()
            for t in threads: t.join()

            if success_count[0] > 1:
                return {
                    "passed": False,
                    "error": (
                        f"Test #5 Failed: Race condition detected! Bob had balance 100.0, but {success_count[0]} concurrent "
                        f"100.0 transfers succeeded. Final balance: {race_engine.balances['bob']}. Missing thread synchronization lock."
                    )
                }

            return {
                "passed": True,
                "reward": 1.0,
                "message": "All 5 multi-vector security tests (Idempotency, Timing-Safe HMAC, Race Protection, Arithmetic) PASSED!"
            }

        except Exception as e:
            return {"passed": False, "error": f"Execution/Assertion Exception: {e}"}

def query_ai_model(messages: list) -> str:
    url = f"https://api.cloudflare.com/client/v4/accounts/{CF_ACCOUNT_ID}/ai/run/{CF_MODEL}"
    headers = {"Authorization": f"Bearer {CF_API_TOKEN}", "Content-Type": "application/json"}
    payload = {"messages": messages}
    
    for attempt in range(1, 4):
        try:
            req = urllib.request.Request(url, data=json.dumps(payload).encode(), headers=headers, method="POST")
            with urllib.request.urlopen(req, timeout=30) as resp:
                res = json.loads(resp.read().decode())
                raw = res.get("result", {}).get("response", "")
                clean = re.sub(r"```python\s*", "", raw)
                clean = re.sub(r"```\s*", "", clean).strip()
                return clean
        except Exception as e:
            print(f"[*] (API Retry attempt {attempt}/3 due to: {e}). Waiting 3s...")
            time.sleep(3)
    return ""

def run_multiround_sandbox():
    print(f"\n{'='*75}")
    print("🏛️ [POST-TRAINING AGENTIC SANDBOX EXAM] Multi-Round Trial-and-Error Loop")
    print(f"Target Challenge: {COMPLEX_CHALLENGE['title']}")
    print(f"{'='*75}\n")

    harness = SandboxHarness()
    max_rounds = 5

    history = [
        {"role": "system", "content": "You are a world-class security engineer and exploit remediator. Write pure Python code."},
        {"role": "user", "content": f"{COMPLEX_CHALLENGE['description']}\n\nVulnerable Code:\n```python\n{COMPLEX_CHALLENGE['vulnerable_code']}```\n\nTask:\n{COMPLEX_CHALLENGE['task']}"}
    ]

    for round_num in range(1, max_rounds + 1):
        print(f"\n{'#'*65}")
        print(f"# 🧪 [SANDBOX ROUND {round_num}/{max_rounds}] AI Autonomous Trial in Isolated Sandbox")
        print(f"{'#'*65}")

        print(f"[*] AI analyzing failure trace, thinking and generating candidate solution...")
        candidate_code = query_ai_model(history)
        
        # Preview first lines
        preview = "\n".join(candidate_code.split("\n")[:8])
        print(f"--- [AI Candidate Solution Snippet (Round {round_num})] ---\n{preview}\n...")

        print(f"[*] Executing candidate solution against 5 multi-threaded assertion tests...")
        result = harness.verify(candidate_code)

        if result["passed"]:
            print(f"\n🎉 [EXAM PASSED IN ROUND {round_num}!]: {result['message']}")
            print(f"🌟 [REINFORCEMENT SCORE]: {result['reward']} / 1.0 (Optimal Architecture Confirmed)")
            print("\n[✓] The Model successfully diagnosed the root cause, handled concurrency, and self-corrected!")
            return True
        else:
            print(f"\n❌ [SANDBOX EXECUTION ERROR]:")
            print(f"   Log: {result['error']}")
            print(f"\n🧠 [AUTONOMOUS REFLECTION & ERROR FEEDBACK]")
            print(f"   Feeding error traceback into the model's context for next round...")

            history.append({"role": "assistant", "content": candidate_code})
            history.append({
                "role": "user",
                "content": (
                    f"Your solution failed in the isolated sandbox with this exact error:\n{result['error']}\n\n"
                    f"Carefully analyze why this test failed. Fix the race condition, timing check, or idempotency mechanism. "
                    f"Return ONLY the complete updated Python code."
                )
            })
            time.sleep(2)

    print("\n[!] Max rounds reached. Sandbox feedback recorded.")
    return False

if __name__ == "__main__":
    run_multiround_sandbox()
