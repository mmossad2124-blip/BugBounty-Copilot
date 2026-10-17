#!/bin/bash
# ==============================================================================
# 🛑 MOSSAD-PENTAST-AI SESSION STOPPER
# Safely terminates local gateways and preserves cloud GPU quota.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PID_FILE="$SCRIPT_DIR/.gateway.pid"

echo "======================================================================"
echo "🛑 STOPPING MOSSAD-PENTAST-AI SESSION"
echo "======================================================================"

# 1. Stop Brain Gateway
if [ -f "$PID_FILE" ]; then
    GATEWAY_PID=$(cat "$PID_FILE")
    if kill -0 $GATEWAY_PID 2>/dev/null; then
        kill $GATEWAY_PID
        echo "[✓] Local Brain Gateway stopped (PID: $GATEWAY_PID)."
    fi
    rm -f "$PID_FILE"
fi

if pgrep -f "brain_gateway.py" > /dev/null; then
    pkill -f "brain_gateway.py"
    echo "[✓] Local Brain Gateway processes terminated."
fi

# 2. Stop OpenHands Docker Container (Free 100% RAM/CPU)
if docker ps -q -f name=openhands-app | grep -q .; then
    echo "[*] Stopping OpenHands Docker Container..."
    docker stop openhands-app > /dev/null
    echo "[✓] OpenHands Docker Container stopped (0% RAM/CPU usage)."
fi

# 3. Stop HexStrike Server if running
if pgrep -f "hexstrike_server.py" > /dev/null; then
    pkill -f "hexstrike_server.py"
    echo "[✓] HexStrike AI Server stopped."
fi

echo "[*] Remember to stop the Kaggle server notebook when finished to preserve GPU hours."
echo "    URL: https://www.kaggle.com/code/mmossad2124/mossad-pentast-ai-server"
echo "======================================================================"
echo "✅ Session ended cleanly. Laptop resources are 100% free for your other projects!"
echo "======================================================================"
