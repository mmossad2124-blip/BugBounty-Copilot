#!/usr/bin/env bash
# ==============================================================================
# BugBounty-Copilot: One-Click Local Launcher
# Runs Streamlit Web UI instantly with zero internet consumption
# ==============================================================================

set -e
REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$REPO_DIR"

echo "=========================================================================="
echo "🛡️  STARTING BUGBOUNTY-COPILOT & HEXSTRIKE AI WEB INTERFACE"
echo "=========================================================================="

# Check if streamlit is in ~/.local/bin or PATH
if command -v streamlit >/dev/null 2>&1; then
    STREAMLIT_BIN="streamlit"
elif [ -f "$HOME/.local/bin/streamlit" ]; then
    STREAMLIT_BIN="$HOME/.local/bin/streamlit"
else
    echo "[!] Streamlit binary not found. Running with python3 -m streamlit..."
    STREAMLIT_BIN="python3 -m streamlit"
fi

echo "[*] Launching Streamlit UI on http://localhost:8501..."
$STREAMLIT_BIN run ui/app.py --server.port 8501 --server.address 0.0.0.0
