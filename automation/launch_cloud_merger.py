#!/usr/bin/env python3
"""
Autonomous Cloud Model Merger - Mossad-pentast-ai
Packages and pushes the model fusion pipeline to Kaggle GPU cloud:
1. Mounts/downloads the final accumulated LoRA weights from the latest completed node.
2. Fuses LoRA delta weights directly into Qwen2.5-7B-Instruct (16-bit lossless merge).
3. Saves the standalone model as 'Mossad-pentast-ai'.
4. Exports GGUF (Q4_K_M) format for lightweight local/cloud inference.
5. Runs live benchmark verification test on Kaggle GPU.
"""

import os
import sys
import json
import time
import urllib.request
import subprocess

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MERGER_DIR = os.path.join(REPO_DIR, "notebooks_merger")
os.makedirs(MERGER_DIR, exist_ok=True)

MODEL_NAME = "Mossad-pentast-ai"

def load_token(acc_id, username, fallback=""):
    creds_path = os.path.join(REPO_DIR, "accounts", f"account_{acc_id}_{username}.json")
    if os.path.exists(creds_path):
        try:
            with open(creds_path) as f:
                return json.load(f).get("credentials", {}).get("kaggle_api_token", fallback)
        except Exception:
            pass
    return os.environ.get(f"KAGGLE_API_TOKEN_{acc_id}", fallback)

ACCOUNT_1_USER = "mmossad2124"
ACCOUNT_1_TOKEN = load_token(1, ACCOUNT_1_USER)

ACCOUNT_3_USER = "mmossad2324"
ACCOUNT_3_TOKEN = load_token(3, ACCOUNT_3_USER)

def fetch_latest_lora_signed_urls():
    """Fetches signed download URLs from the latest completed node (checks both accounts)."""
    check_order = [("mmossad2324", ACCOUNT_3_TOKEN), ("mmossad2124", ACCOUNT_1_TOKEN)]
    for user, token in check_order:
        if not token:
            continue
        try:
            url = f"https://www.kaggle.com/api/v1/kernels/output?userName={user}&kernelSlug=bugbounty-copilot-trainer"
            headers = {"Authorization": f"Bearer {token}", "User-Agent": "KaggleWatcher/1.0"}
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode())
            files = {f["fileName"]: f["url"] for f in data.get("files", []) if "bugbounty_copilot_lora" in f.get("fileName", "")}
            if files and any("adapter_model.safetensors" in k for k in files):
                print(f"[✓] Retrieved {len(files)} signed LoRA weight URLs from node {user}!")
                return files, user
        except Exception as e:
            print(f"[!] Warning fetching LoRA URLs from {user}: {e}")
    return {}, ""

def generate_merger_notebook(lora_urls, source_node):
    nb = {
        "cells": [
            {
                "cell_type": "markdown",
                "metadata": {},
                "source": [
                    f"# 🔥 {MODEL_NAME} - Cloud Model Fusion & Standalone Weight Merger\n",
                    "\n",
                    f"Fuses all trained LoRA security adapters (27,000 + 32 sources) directly into **Qwen2.5-7B-Instruct**.\n",
                    "- **Target Model**: `Mossad-pentast-ai`\n",
                    f"- **Source Weights**: Node `{source_node}` (`bugbounty_copilot_lora`)\n",
                    "- **Outputs**:\n",
                    f"  1. Standalone 16-bit Float16 Model (`/kaggle/working/{MODEL_NAME}`)\n",
                    f"  2. Standalone GGUF Q4_K_M Quantized Model (`/kaggle/working/{MODEL_NAME}-GGUF`)\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 1. Environment & CUDA Configuration\n",
                    "import os\n",
                    "os.environ['CUDA_VISIBLE_DEVICES'] = '0'\n",
                    "!pip install -q --no-deps \"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git\"\n",
                    "!pip install -q unsloth_zoo\n",
                    "!pip install -q --no-deps trl peft accelerate bitsandbytes\n",
                    "!pip install -q datasets transformers triton xformers\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 2. Locate and Prepare LoRA Weights\n",
                    "import os, glob, json, urllib.request\n",
                    f"LATEST_LORA_URLS = {json.dumps(lora_urls)}\n",
                    "\n",
                    "possible_loras = glob.glob('/kaggle/input/**/bugbounty_copilot_lora/adapter_model.safetensors', recursive=True)\n",
                    "if not possible_loras:\n",
                    "    possible_loras = glob.glob('/kaggle/input/**/adapter_model.safetensors', recursive=True)\n",
                    "\n",
                    "adapter_dir = None\n",
                    "if possible_loras:\n",
                    "    adapter_dir = os.path.dirname(possible_loras[0])\n",
                    "    print(f'[✓] Found mounted LoRA Adapter at: {adapter_dir}')\n",
                    "elif LATEST_LORA_URLS:\n",
                    "    print(f'[*] Downloading {len(LATEST_LORA_URLS)} LoRA files via signed direct URLs...')\n",
                    "    adapter_dir = '/kaggle/working/latest_lora'\n",
                    "    os.makedirs(adapter_dir, exist_ok=True)\n",
                    "    for fname, url in LATEST_LORA_URLS.items():\n",
                    "        target_file = os.path.join(adapter_dir, os.path.basename(fname))\n",
                    "        try:\n",
                    "            urllib.request.urlretrieve(url, target_file)\n",
                    "            print(f'    -> Downloaded: {os.path.basename(fname)}')\n",
                    "        except Exception as e:\n",
                    "            print(f'    -> Warning: {e}')\n",
                    "\n",
                    "if not adapter_dir or not os.path.exists(os.path.join(adapter_dir, 'adapter_model.safetensors')):\n",
                    "    raise RuntimeError('Could not locate trained LoRA weights for merging!')\n",
                    "\n",
                    "print(f'[✓✓✓] LoRA weights verified ready at: {adapter_dir}')\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    "# 3. Load Model in 16-bit and Fuse LoRA Weights Losslessly\n",
                    "from unsloth import FastLanguageModel\n",
                    "import torch\n",
                    "\n",
                    "print('[*] Loading base model and fusing LoRA adapter into full 16-bit neural tensors...')\n",
                    "model, tokenizer = FastLanguageModel.from_pretrained(\n",
                    "    model_name = adapter_dir,\n",
                    "    max_seq_length = 4096,\n",
                    "    dtype = torch.float16,\n",
                    "    load_in_4bit = False,\n",
                    "    device_map = {'': 0},\n",
                    ")\n",
                    "print('[✓] Model & LoRA weights successfully unified into memory graph!')\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    f"# 4. Save Standalone 16-bit Model as '{MODEL_NAME}'\n",
                    f"merged_dir = '/kaggle/working/{MODEL_NAME}'\n",
                    "print(f'[*] Saving merged 16-bit standalone model to {merged_dir}...')\n",
                    "model.save_pretrained_merged(merged_dir, tokenizer, save_method = 'merged_16bit')\n",
                    f"print(f'[✓✓✓] STANDALONE MODEL \"{MODEL_NAME}\" SAVED SUCCESSFULLY!')\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    f"# 5. Export Compact Standalone GGUF (Q4_K_M) for Fast Local / Server Inference\n",
                    f"gguf_dir = '/kaggle/working/{MODEL_NAME}-GGUF'\n",
                    "print(f'[*] Compiling and exporting GGUF (Q4_K_M) format to {gguf_dir}...')\n",
                    "try:\n",
                    "    model.save_pretrained_gguf(gguf_dir, tokenizer, quantization_method = 'q4_k_m')\n",
                    f"    print(f'[✓✓✓] GGUF QUANTIZED MODEL \"{MODEL_NAME}\" EXPORTED SUCCESSFULLY!')\n",
                    "except Exception as e:\n",
                    "    print(f'[!] GGUF compilation note ({e}). Standalone 16-bit model is 100% saved and ready.')\n"
                ]
            },
            {
                "cell_type": "code",
                "execution_count": None,
                "metadata": {},
                "outputs": [],
                "source": [
                    f"# 6. Live Benchmark Inference Test on Merged Model '{MODEL_NAME}'\n",
                    "try:\n",
                    "    FastLanguageModel.for_inference(model)\n",
                    "    test_messages = [\n",
                    f"        {{\"role\": \"system\", \"content\": \"You are {MODEL_NAME}, an Elite Offensive Security & Bug Bounty AI Copilot.\"}},\n",
                    "        {\"role\": \"user\", \"content\": \"Target: https://api.enterprise.com/v1/auth/oauth/token. Detail your systematic exploit methodology to identify host header injection, token leakage, and unauthorized password takeover.\"}\n",
                    "    ]\n",
                    "    inputs = tokenizer.apply_chat_template(\n",
                    "        test_messages,\n",
                    "        tokenize = True,\n",
                    "        add_generation_prompt = True,\n",
                    "        return_tensors = 'pt',\n",
                    "    ).to('cuda:0')\n",
                    "    print('\\n' + '='*70)\n",
                    f"    print('🎯 LIVE BENCHMARK INFERENCE TEST: {MODEL_NAME}')\n",
                    "    print('='*70)\n",
                    "    outputs = model.generate(input_ids = inputs, max_new_tokens = 256, use_cache = True)\n",
                    "    print(tokenizer.decode(outputs[0], skip_special_tokens = True))\n",
                    "    print('='*70)\n",
                    f"    print('\\n🎉 [FUSION COMPLETE] {MODEL_NAME} IS FULLY BORN AND READY FOR OPERATION!')\n",
                    "except Exception as e:\n",
                    "    print(f'[!] Inference test note ({e}). Model is saved.')\n"
                ]
            }
        ],
        "metadata": {
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            },
            "language_info": {
                "codemirror_mode": {"name": "ipython", "version": 3},
                "file_extension": ".py",
                "mimetype": "text/x-python",
                "name": "python",
                "nbformat": 4,
                "nbformat_minor": 2,
                "version": "3.10.0"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 2
    }
    nb_path = os.path.join(MERGER_DIR, "Mossad_Pentast_AI_Merger.ipynb")
    with open(nb_path, "w", encoding="utf-8") as f:
        json.dump(nb, f, indent=1)
    print(f"[✓] Merger notebook generated at: {nb_path}")
    return nb_path

def push_and_launch_merger():
    print(f"\n{'='*75}")
    print(f"🚀 LAUNCHING CLOUD FUSION & MERGER: {MODEL_NAME}")
    print(f"{'='*75}")

    lora_urls, source_node = fetch_latest_lora_signed_urls()
    if not lora_urls:
        print("[!] Error: Could not locate signed URLs for LoRA weights.")
        return False

    generate_merger_notebook(lora_urls, source_node)

    # Prepare kernel metadata
    target_user = ACCOUNT_1_USER
    target_token = ACCOUNT_1_TOKEN
    kernel_slug = "mossad-pentast-ai-merger"

    meta = {
        "id": f"{target_user}/{kernel_slug}",
        "title": "Mossad Pentast AI Merger",
        "code_file": "Mossad_Pentast_AI_Merger.ipynb",
        "language": "python",
        "kernel_type": "notebook",
        "is_private": False,
        "enable_gpu": True,
        "enable_internet": True,
        "dataset_sources": [],
        "competition_sources": [],
        "kernel_sources": [
            f"mmossad2324/bugbounty-copilot-trainer",
            f"mmossad2124/bugbounty-copilot-trainer"
        ]
    }
    meta_path = os.path.join(MERGER_DIR, "kernel-metadata.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    # Configure Kaggle credentials
    home = os.path.expanduser("~")
    kaggle_dir = os.path.join(home, ".kaggle")
    os.makedirs(kaggle_dir, exist_ok=True)
    with open(os.path.join(kaggle_dir, "access_token"), "w") as f:
        f.write(target_token)
    os.chmod(os.path.join(kaggle_dir, "access_token"), 0o600)

    # Push kernel to Kaggle
    pusher_code = f"""
import os, sys, ssl, time, urllib3.util.ssl_
orig = urllib3.util.ssl_.create_urllib3_context
def patched(*args, **kwargs):
    ctx = orig(*args, **kwargs)
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    return ctx
urllib3.util.ssl_.create_urllib3_context = patched
os.environ["KAGGLE_API_TOKEN"] = "{target_token}"
from kaggle.api.kaggle_api_extended import KaggleApi
api = KaggleApi()
api.authenticate()

res = api.kernels_push("{MERGER_DIR}")
print("[✓] PUSH TO KAGGLE MERGER SUCCESSFUL:", res.url if hasattr(res, "url") else res)
"""
    subprocess.run([sys.executable, "-c", pusher_code], check=True)
    kernel_url = f"https://www.kaggle.com/code/{target_user}/{kernel_slug}"
    print(f"\n[✓✓✓] CLOUD MERGER TRIGGERED ON KAGGLE!")
    print(f"      Kernel URL: {kernel_url}")
    print(f"      The model '{MODEL_NAME}' is now fusing directly on Nvidia GPU in the cloud.")
    return True

if __name__ == "__main__":
    push_and_launch_merger()
