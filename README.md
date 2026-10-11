# 🛡️ Bug Bounty Copilot - Autonomous Self-Evolving LLM

An autonomous, cloud-native offensive security AI system designed for **continuous self-evolution** using **Unsloth (QLoRA 4-bit)** on **Kaggle T4 GPUs**.

---

## 🏗️ Architecture & Cloud Infrastructure

```
┌────────────────────────────────────────────────────────────────────────┐
│                        Autonomous 24/7 Pipeline                        │
├────────────────────────────────────────────────────────────────────────┤
│ 1. GitHub Actions (Cron @ 02:00 AM UTC):                               │
│    - Scrapes 6,400+ curated real-world disclosures (PentesterLand).    │
│    - Structures reports into Chain-of-Thought (CoT) reasoning pairs.   │
│                                                                        │
│ 2. Kaggle Background Runner (T4 GPU - Unattended):                     │
│    - Triggered via Kaggle API (`kaggle kernels push`).                 │
│    - Trains Qwen2.5-7B with Unsloth in ~1-2 hours.                     │
│    - Saves LoRA weights without local PC or browser running.           │
│                                                                        │
│ 3. 3-Account Multi-GPU Cluster (90 Hours/Week):                        │
│    - Account 1: Primary SFT fine-tuning.                               │
│    - Account 2: DPO preference alignment & evaluation.                 │
│    - Account 3: Daily automation scheduler & scraping.                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
BugBounty-Copilot/
├── accounts/                  # Credentials & Role Mapping (Secured)
│   ├── account_1_mmossad2124.json   # Primary Orchestrator & Token 1
│   ├── account_2_mmossad2224.json   # Datasets Engine & Token 2
│   └── account_3_mmossad2324.json   # Automation Scheduler & Token 3
├── data_pipeline/
│   ├── fetch_elite_writeups.py      # Scraper for 6,400+ high-signal writeups
│   └── processed_datasets/
│       └── elite_bugbounty_cot.jsonl # Generated CoT training dataset
├── notebooks/
│   ├── BugBounty_Copilot_Kaggle_Trainer.ipynb # Unsloth T4 Kaggle Notebook
│   └── kernel-metadata.json         # Kaggle API metadata
└── automation/
    └── daily_kaggle_train.yml       # GitHub Actions 24/7 cron workflow
```

---

## 🚀 How to Run

### Method 1: Manual One-Click on Kaggle
1. Upload `BugBounty_Copilot_Kaggle_Trainer.ipynb` to [Kaggle Code](https://www.kaggle.com/code).
2. Set Accelerator to **GPU T4 x2**.
3. Turn **Internet ON**.
4. Click **Save Version > Save & Run All (Commit)** — and close your browser! It will train in the background.

### Method 2: Automated via GitHub Actions
1. Push this repository to GitHub Account 1 (`mmossad2124-blip`).
2. Add `KAGGLE_API_TOKEN_1` to Repository Secrets.
3. The workflow will run every day at 02:00 UTC automatically!
