#!/bin/bash
set -e

echo "[*] 1/4 Installing Flowise components dependencies..."
cd /tools/node/lib/node_modules/flowise
npm install --legacy-peer-deps multer-s3 winston-daily-rotate-file turndown langchainhub >/dev/null 2>&1 || npm install multer-s3 winston-daily-rotate-file turndown langchainhub >/dev/null 2>&1 || true

echo "[*] 2/4 Stopping any stale processes on port 3000..."
fuser -k 3000/tcp >/dev/null 2>&1 || true
sleep 1

echo "[*] 3/4 Launching Flowise on native storage (/content/flowise_native)..."
export FLOWISE_DATA_DIR="/content/flowise_native"
export DATABASE_PATH="/content/flowise_native"
export APIKEY_PATH="/content/flowise_native"
export SECRETKEY_PATH="/content/flowise_native"
export LOG_PATH="/content/flowise_native/logs"
export BLOB_STORAGE_PATH="/content/flowise_native/storage"
export TOOL_FUNCTION_BUILTIN_DEP="child_process,path,buffer,fs,http,https"
export ALLOW_BUILTIN_DEP="true"
export TOOL_FUNCTION_EXTERNAL_DEP="node-fetch,axios"
export PORT="3000"

nohup /tools/node/bin/flowise start > /content/flowise_native/logs/flowise.log 2>&1 &
FLOWISE_PID=$!
echo "[✓] Flowise spawned with PID: $FLOWISE_PID"

echo "[*] 4/4 Waiting for Flowise Web UI to be ready on port 3000..."
READY=0
for i in $(seq 1 45); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/api/v1/ping || true)
    if [ "$STATUS" = "200" ]; then
        READY=1
        break
    fi
    sleep 2
done

if [ "$READY" = "1" ]; then
    echo "[✓✓✓] FLOWISE IS FULLY ONLINE AND HEALTHY (HTTP 200)!"
    python3 - << 'PYEOF'
import requests, json, time

session = requests.Session()
f_headers = {"x-request-from": "internal", "Content-Type": "application/json"}
ADMIN_EMAIL = "mossad@pentast.ai"
ADMIN_PASS = "Mossad724*"
ADMIN_NAME = "Mossad"

def try_login():
    for p in [{"email": ADMIN_EMAIL, "password": ADMIN_PASS}, {"email": ADMIN_EMAIL, "credential": ADMIN_PASS}]:
        try:
            r = session.post("http://127.0.0.1:3000/api/v1/auth/login", json=p, headers=f_headers, timeout=5)
            if r.status_code in (200, 201):
                return r
        except Exception:
            pass
    return None

r_log = try_login()
if not r_log:
    print("[*] Registering Flowise Root Administrator account...")
    for rp in [
        {"user": {"name": ADMIN_NAME, "email": ADMIN_EMAIL, "credential": ADMIN_PASS}},
        {"user": {"name": ADMIN_NAME, "email": ADMIN_EMAIL, "password": ADMIN_PASS}},
        {"user": {"name": ADMIN_NAME, "email": ADMIN_EMAIL, "credential": ADMIN_PASS, "confirmPassword": ADMIN_PASS}},
    ]:
        try:
            rr = session.post("http://127.0.0.1:3000/api/v1/account/register", json=rp, headers=f_headers, timeout=10)
            if rr.status_code in (200, 201):
                print(f"[✓] Registration successful (HTTP {rr.status_code})")
                break
        except Exception as e:
            pass
    r_log = try_login()

if r_log and r_log.status_code in (200, 201):
    print("[✓✓✓] Flowise Root Admin Authenticated Successfully!")
else:
    print("[!] Flowise setup status:", r_log.status_code if r_log else "Not registered")
PYEOF
else
    echo "[!] Flowise failed to respond within 90s. Last log lines:"
    tail -n 25 /content/flowise_native/logs/flowise.log
    exit 1
fi
