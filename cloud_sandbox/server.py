"""
Mossad-Pentast-AI Cloud Sandbox Execution Server (FastAPI)
Runs inside GitHub Codespaces (or any cloud VM) on port 8000.
Receives cyber reconnaissance / dev commands from Kaggle Brain or Local OpenHands Cockpit,
executes them at 10 Gbps cloud speed, and streams/returns the live terminal output.
"""

import os
import subprocess
import time
from typing import Optional
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

app = FastAPI(
    title="Mossad-Pentast-AI Cloud Sandbox API",
    description="Remote high-speed execution sandbox for GitHub Codespaces & Kaggle AI Agent",
    version="2.0.0",
)

SANDBOX_API_KEY = os.environ.get("SANDBOX_API_KEY", "sk-mossad-pentast-2026")
WORKSPACE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


class CommandRequest(BaseModel):
    command: str
    timeout: Optional[int] = 120
    cwd: Optional[str] = None


@app.get("/health")
def health_check():
    return {
        "status": "online",
        "sandbox": "GitHub Codespaces / Cloud VM",
        "workspace": WORKSPACE_DIR,
    }


@app.post("/execute")
def execute_command(
    req: CommandRequest,
    authorization: Optional[str] = Header(default=None),
):
    if authorization and f"Bearer {SANDBOX_API_KEY}" != authorization:
        raise HTTPException(status_code=401, detail="Unauthorized Sandbox Key")

    work_dir = req.cwd or WORKSPACE_DIR
    print(f"\n[⚡ CLOUD SANDBOX EXECUTING]: {req.command}")
    start_ts = time.time()
    try:
        proc = subprocess.run(
            req.command,
            shell=True,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=req.timeout or 120,
        )
        elapsed = round(time.time() - start_ts, 2)
        print(f"[✓ COMPLETED in {elapsed}s | Exit Code: {proc.returncode}]")
        if proc.stdout:
            print(proc.stdout[:1000])
        return {
            "status": "completed",
            "command": req.command,
            "exit_code": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "elapsed_seconds": elapsed,
        }
    except subprocess.TimeoutExpired:
        return {
            "status": "timeout",
            "command": req.command,
            "exit_code": 124,
            "stdout": "",
            "stderr": f"Command timed out after {req.timeout}s",
            "elapsed_seconds": req.timeout,
        }
    except Exception as e:
        return {
            "status": "error",
            "command": req.command,
            "exit_code": 1,
            "stdout": "",
            "stderr": str(e),
            "elapsed_seconds": round(time.time() - start_ts, 2),
        }
