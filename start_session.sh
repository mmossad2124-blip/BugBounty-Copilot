#!/bin/bash
# ==============================================================================
# 🚀 MOSSAD-PENTAST-AI AUTONOMOUS SESSION CONDUCTOR
# 1. Launches Local Brain Gateway with Automatic Failover (Port 8080)
# 2. Checks/Queries Cloud GPU Brain on Kaggle
# 3. Ready for OpenHands, Cline, Antigravity, or CLI Agent!
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="$SCRIPT_DIR/venv/bin/python3"
GATEWAY_SCRIPT="$SCRIPT_DIR/automation/brain_gateway.py"
PID_FILE="$SCRIPT_DIR/.gateway.pid"

echo "======================================================================"
echo "🎯 STARTING MOSSAD-PENTAST-AI AUTONOMOUS SESSION"
echo "======================================================================"

# 1. Start Brain Gateway if not already running
if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
    echo "[✓] Local Brain Gateway is already active on http://127.0.0.1:8080/v1 (PID: $(cat "$PID_FILE"))"
elif pgrep -f "brain_gateway.py" > /dev/null; then
    echo "[✓] Local Brain Gateway is already active on http://127.0.0.1:8080/v1"
else
    echo "[*] Launching Local Brain Gateway..."
    "$PYTHON_BIN" "$GATEWAY_SCRIPT" > "$SCRIPT_DIR/brain_gateway.log" 2>&1 &
    GATEWAY_PID=$!
    echo $GATEWAY_PID > "$PID_FILE"
    sleep 2
    if kill -0 $GATEWAY_PID 2>/dev/null; then
        echo "[✓] Brain Gateway successfully started on http://127.0.0.1:8080/v1 (PID: $GATEWAY_PID)"
    else
        echo "[!] Warning: Brain Gateway failed to start. Check brain_gateway.log"
    fi
fi

# 2. Start OpenHands Container on demand
echo "[*] Starting OpenHands Docker Cockpit (Port 3000)..."
if docker ps -q -f name=openhands-app | grep -q .; then
    echo "[✓] OpenHands container is already running on http://localhost:3000"
elif docker ps -aq -f name=openhands-app | grep -q .; then
    docker start openhands-app > /dev/null
    sleep 2
    echo "[✓] OpenHands container started on http://localhost:3000"
else
    "$SCRIPT_DIR/launch_openhands.sh"
fi

# Ensure internal action execution server (Port 30001) is running inside openhands-app
if ! docker exec openhands-app curl -s http://127.0.0.1:30001/alive > /dev/null 2>&1; then
    echo "[*] Starting internal sandbox execution engine (Port 30001)..."
    docker exec -d openhands-app bash -c "python3 -u -m openhands.runtime.action_execution_server 30001 --working-dir /opt/workspace_base --username root --user-id 0 > /tmp/action_server.log 2>&1"
fi

# 3. Check & Auto-Launch Kaggle GPU Brain (Mossad-pentast-ai)
echo "[*] Querying Cloud GPU Brain (Kaggle T4 - Mossad-pentast-ai)..."
KAGGLE_STATUS=$("$PYTHON_BIN" -c "
import os, json, subprocess
acc1 = json.load(open('$SCRIPT_DIR/accounts/account_1_mmossad2124.json'))
tok = acc1['credentials']['kaggle_api_token']
os.makedirs(os.path.expanduser('~/.kaggle'), exist_ok=True)
with open(os.path.expanduser('~/.kaggle/access_token'), 'w') as f:
    f.write(tok)
os.chmod(os.path.expanduser('~/.kaggle/access_token'), 0o600)
p = subprocess.run(['$SCRIPT_DIR/venv/bin/kaggle', 'kernels', 'status', 'mmossad2124/mossad-pentast-ai-server'], capture_output=True, text=True)
print(p.stdout.strip())
" 2>/dev/null)

echo "    Kaggle Status: $KAGGLE_STATUS"
if [[ "$KAGGLE_STATUS" != *"RUNNING"* ]]; then
    echo "[*] Kaggle GPU Server is stopped. Launching Mossad-pentast-ai on Kaggle GPU now..."
    "$PYTHON_BIN" -c "
import os, json, ssl, urllib3.util.ssl_
orig = urllib3.util.ssl_.create_urllib3_context
def patched(*args, **kwargs):
    ctx = orig(*args, **kwargs)
    ctx.set_ciphers('DEFAULT@SECLEVEL=1')
    return ctx
urllib3.util.ssl_.create_urllib3_context = patched
acc1 = json.load(open('$SCRIPT_DIR/accounts/account_1_mmossad2124.json'))
os.environ['KAGGLE_API_TOKEN'] = acc1['credentials']['kaggle_api_token']
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()
api.kernels_push('$SCRIPT_DIR/notebooks_server')
print('    [✓] Mossad-pentast-ai launched on Kaggle T4 GPU!')
"
fi

# 4. Instructions & Ready State
echo "======================================================================"
echo "🎉 SYSTEM FULLY INITIALIZED AND READY FOR ACTION!"
echo "======================================================================"
echo "🌐 OpenHands Cockpit UI:                http://localhost:3000"
echo "🔗 Brain Endpoint (Local Gateway):      http://127.0.0.1:8080/v1"
echo "🔑 API Key:                             sk-mossad-pentast-2026"
echo "🧠 Exclusive Model:                     Mossad-pentast-ai (1. Kaggle GPU -> 2. HuggingFace)"
echo "🛑 To stop everything & free RAM:       ./stop_session.sh"
echo "======================================================================"
