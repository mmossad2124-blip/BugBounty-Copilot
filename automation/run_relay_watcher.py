#!/usr/bin/env python3
import time, os, sys

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_DIR)

from automation.autonomous_relay_daemon import (
    wait_for_kernel_completion, trigger_kaggle_kernel,
    ACCOUNT_1_USER, ACCOUNT_1_TOKEN, ACCOUNT_3_USER, ACCOUNT_3_TOKEN
)

def main():
    print(f"\n{'='*70}")
    print("🚀 [RELAY WATCHER] Monitoring Account 1 (mmossad2124) Stage 1 Training...")
    print(f"{'='*70}")
    
    success = wait_for_kernel_completion(ACCOUNT_1_USER, ACCOUNT_1_TOKEN, max_wait_hours=3)
    if success:
        print(f"\n{'='*70}")
        print("🎯 [HANDOFF] Account 1 Complete! Waking Up Account 3 for Stage 2...")
        print(f"{'='*70}")
        trigger_kaggle_kernel(ACCOUNT_3_USER, ACCOUNT_3_TOKEN)
        acc3_success = wait_for_kernel_completion(ACCOUNT_3_USER, ACCOUNT_3_TOKEN, max_wait_hours=3)
        if acc3_success:
            print("\n[✓✓✓] FULL INDUSTRIAL RELAY COMPLETE ACROSS BOTH ACCOUNTS!")
        else:
            print("\n[!] Account 3 finished with warnings or error.")
    else:
        print("\n[!] Account 1 did not complete cleanly.")

if __name__ == "__main__":
    main()
