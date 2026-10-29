#!/bin/bash

echo "[*] Diagnostic: Checking current Flowise error in log..."
grep -E "Cannot find module|MODULE_NOT_FOUND" -C 2 /content/flowise_native/logs/flowise.log || head -n 15 /content/flowise_native/logs/flowise.log || true

echo "[*] Setting comprehensive NODE_PATH..."
export NODE_PATH="/tools/node/lib/node_modules/flowise/node_modules:/tools/node/lib/node_modules:/tools/node/lib/node_modules/flowise/node_modules/flowise-components/node_modules"

echo "[*] Auto-resolving all storage dependencies via automated loader loop..."
python3 - << 'PYEOF'
import subprocess, re, sys

storage_index = "/tools/node/lib/node_modules/flowise/node_modules/flowise-components/dist/src/storage/index.js"
node_dirs = [
    "/tools/node/lib/node_modules/flowise/node_modules/flowise-components",
    "/tools/node/lib/node_modules/flowise"
]
env = dict(PATH="/tools/node/bin:/usr/local/cuda/bin:/usr/local/bin:/usr/bin:/bin",
           NODE_PATH="/tools/node/lib/node_modules/flowise/node_modules:/tools/node/lib/node_modules:/tools/node/lib/node_modules/flowise/node_modules/flowise-components/node_modules")

# Pre-install known storage packages
known = ["winston-azure-blob", "multer-azure-blob-storage", "multer-cloud-storage", "s3-streamlogger", "@azure/storage-blob", "@google-cloud/logging-winston", "@google-cloud/storage", "@aws-sdk/client-s3", "sanitize-filename", "winston-daily-rotate-file", "turndown", "@langchain/core"]
print("[*] Installing batch of known storage packages...")
for d in node_dirs:
    subprocess.run(["npm", "install", "--legacy-peer-deps"] + known, cwd=d, env=env, capture_output=True)

for attempt in range(15):
    res = subprocess.run(["node", "-e", f"require('{storage_index}')"], env=env, capture_output=True, text=True)
    if res.returncode == 0:
        print(f"[✓✓✓] Storage index loaded successfully with 0 errors on attempt {attempt+1}!")
        sys.exit(0)
    m = re.search(r"Cannot find module '([^']+)'", res.stderr)
    if m:
        missing = m.group(1)
        print(f"[*] Missing package detected: {missing}. Installing into node dirs...")
        for d in node_dirs:
            subprocess.run(["npm", "install", "--legacy-peer-deps", missing], cwd=d, env=env, capture_output=True)
    else:
        print("[!] Error loading storage index:", res.stderr[:300])
        break
PYEOF

echo "[*] Stopping any existing process on port 3000..."
fuser -k 3000/tcp >/dev/null 2>&1 || true
sleep 1

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

echo "[*] Starting Flowise..."
> /content/flowise_native/logs/flowise.log
nohup /tools/node/bin/flowise start > /content/flowise_native/logs/flowise.log 2>&1 &
FLOWISE_PID=$!
echo "[✓] Flowise spawned with PID: $FLOWISE_PID"

echo "[*] Waiting for Flowise..."
READY=0
for i in $(seq 1 30); do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:3000/api/v1/ping || true)
    if [ "$STATUS" = "200" ]; then
        READY=1
        break
    fi
    sleep 2
done

if [ "$READY" = "1" ]; then
    echo "[✓✓✓] FLOWISE IS ONLINE AND RESPONDING 200 OK!"
    python3 - << 'PYEOF'
import requests, json

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
    print("[*] Registering Administrator...")
    for rp in [
        {"user": {"name": ADMIN_NAME, "email": ADMIN_EMAIL, "credential": ADMIN_PASS}},
        {"user": {"name": ADMIN_NAME, "email": ADMIN_EMAIL, "password": ADMIN_PASS}},
    ]:
        try:
            rr = session.post("http://127.0.0.1:3000/api/v1/account/register", json=rp, headers=f_headers, timeout=10)
            if rr.status_code in (200, 201):
                print(f"[✓] Registration successful (HTTP {rr.status_code})")
                break
        except Exception:
            pass
    r_log = try_login()

if r_log and r_log.status_code in (200, 201):
    print("[✓✓✓] Flowise Admin Authenticated Successfully!")
else:
    print("[!] Login status:", r_log.status_code if r_log else "None")
PYEOF
else
    echo "[!] Flowise failed to start. Current log:"
    cat /content/flowise_native/logs/flowise.log | head -n 30
fi
