#!/bin/bash
# ==============================================================================
# 🚀 LAUNCH OPENHANDS AUTONOMOUS AGENT WORKSPACE
# Connects OpenHands to Mossad-pentast-ai via Local Gateway (Port 8080)
# Exposes Web Cockpit on http://localhost:3000
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "======================================================================"
echo "🚀 INITIALIZING OPENHANDS AUTONOMOUS COCKPIT"
echo "======================================================================"

# Check if openhands container already running
if docker ps -q -f name=openhands-app | grep -q .; then
    echo "[✓] OpenHands is already running on http://localhost:3000"
    exit 0
fi

# Remove stopped container if exists
if docker ps -aq -f name=openhands-app | grep -q .; then
    echo "[*] Removing stopped container instance..."
    docker rm openhands-app > /dev/null 2>&1
fi

echo "[*] Starting OpenHands container..."
docker run -d \
    --name openhands-app \
    -p 3000:3000 \
    --add-host host.docker.internal:host-gateway \
    -e SANDBOX_USER_ID=$(id -u) \
    -e SANDBOX_RUNTIME_CONTAINER_IMAGE="ghcr.io/all-hands-ai/runtime:0.14-nikolaik" \
    -e PERSIST_SANDBOX="true" \
    -e LLM_BASE_URL="http://host.docker.internal:8080/v1" \
    -e LLM_API_KEY="sk-mossad-pentast-2026" \
    -e LLM_MODEL="openai/Mossad-pentast-ai" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$SCRIPT_DIR":/opt/workspace_base \
    -v "$HOME/.openhands-state":/.openhands-state \
    ghcr.io/all-hands-ai/openhands:0.14

sleep 3

if docker ps -q -f name=openhands-app | grep -q .; then
    echo "======================================================================"
    echo "🎉 OPENHANDS IS LIVE AND READY!"
    echo "======================================================================"
    echo "🌐 Access OpenHands Cockpit: http://localhost:3000"
    echo "🧠 Connected Brain:          Mossad-pentast-ai (via http://127.0.0.1:8080/v1)"
    echo "📁 Workspace Mounted:        $SCRIPT_DIR"
    echo "======================================================================"
else
    echo "[!] Container launch notice. Check: docker logs openhands-app"
fi
