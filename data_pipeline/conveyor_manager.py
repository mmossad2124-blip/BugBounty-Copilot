#!/usr/bin/env python3
"""
Continuous Industrial Conveyor-Belt Dataset Manager
Handles progressive pagination through the 27,000 samples across consecutive cycles.
Injects a 20% Replay Buffer of foundational historic milestones to prevent catastrophic forgetting.
"""

import os
import sys
import json
import random
import time

REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATASETS_DIR = os.path.join(REPO_DIR, "data_pipeline", "processed_datasets")
CURSOR_PATH = os.path.join(REPO_DIR, "data_pipeline", "conveyor_cursor.json")

STAGE1_FULL = os.path.join(DATASETS_DIR, "stage1_web_cloud_arsenal.jsonl")
STAGE2_FULL = os.path.join(DATASETS_DIR, "stage2_kernel_apt_arsenal.jsonl")
REPLAY_SOURCE = os.path.join(DATASETS_DIR, "legendary_milestones_curated.jsonl")

STAGE1_ACTIVE_CHUNK = os.path.join(DATASETS_DIR, "active_stage1_chunk.jsonl")
STAGE2_ACTIVE_CHUNK = os.path.join(DATASETS_DIR, "active_stage2_chunk.jsonl")

DEFAULT_CURSOR = {
    "stage1": {
        "total_samples": 20895,
        "chunk_size": 2400,
        "replay_size": 480,
        "new_samples_per_chunk": 1920,
        "current_offset": 0,
        "completed_cycles": 0,
        "total_cycles_needed": 11,
        "is_completed": False
    },
    "stage2": {
        "total_samples": 6022,
        "chunk_size": 2400,
        "replay_size": 480,
        "new_samples_per_chunk": 1920,
        "current_offset": 0,
        "completed_cycles": 0,
        "total_cycles_needed": 4,
        "is_completed": False
    },
    "overall_epoch": 1,
    "last_updated": None
}

def load_cursor():
    if os.path.exists(CURSOR_PATH):
        try:
            with open(CURSOR_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return json.loads(json.dumps(DEFAULT_CURSOR))

def save_cursor(cursor):
    cursor["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    with open(CURSOR_PATH, "w", encoding="utf-8") as f:
        json.dump(cursor, f, indent=2)

def load_replay_samples(count, seed=3407):
    """Loads a random slice of foundational historic milestones to prevent forgetting."""
    milestones = []
    if os.path.exists(REPLAY_SOURCE):
        with open(REPLAY_SOURCE, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    try:
                        milestones.append(json.loads(line.strip()))
                    except Exception:
                        pass
    if not milestones:
        return []
    rng = random.Random(seed)
    rng.shuffle(milestones)
    return milestones[:count]

def slice_file_lines(filepath, offset, count):
    """Extracts a continuous slice of lines from a large JSONL file."""
    lines = []
    total_found = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            if idx >= offset and len(lines) < count:
                if line.strip():
                    try:
                        lines.append(json.loads(line.strip()))
                    except Exception:
                        pass
            total_found = idx + 1
    return lines, total_found

def prepare_active_chunks():
    """Builds active training chunks for both accounts with 80% new data + 20% replay buffer."""
    cursor = load_cursor()
    s1_cfg = cursor["stage1"]
    s2_cfg = cursor["stage2"]

    print(f"\n{'='*75}")
    print(f"🏭 [CONVEYOR MANAGER] Preparing Training Chunks (Cycle {s1_cfg['completed_cycles'] + 1})")
    print(f"{'='*75}")

    # 1. Stage 1 Slice (Account 1: mmossad2124)
    s1_new, s1_total = slice_file_lines(STAGE1_FULL, s1_cfg["current_offset"], s1_cfg["new_samples_per_chunk"])
    s1_cfg["total_samples"] = s1_total
    
    # If wrapped around or near end
    if len(s1_new) < s1_cfg["new_samples_per_chunk"]:
        # Wrap around from beginning
        remaining_needed = s1_cfg["new_samples_per_chunk"] - len(s1_new)
        wrap_slice, _ = slice_file_lines(STAGE1_FULL, 0, remaining_needed)
        s1_new.extend(wrap_slice)
        s1_cfg["is_completed"] = True
        print(f"[!] Stage 1 reached full coverage! Wrapping into next epoch review.")

    s1_replay = load_replay_samples(s1_cfg["replay_size"], seed=s1_cfg["completed_cycles"] + 100)
    s1_final = s1_new + s1_replay
    random.shuffle(s1_final)

    with open(STAGE1_ACTIVE_CHUNK, "w", encoding="utf-8") as f:
        for item in s1_final:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[✓] Stage 1 Chunk Prepared: {len(s1_final)} samples ({len(s1_new)} fresh + {len(s1_replay)} replay)")
    print(f"    - Current Range: [{s1_cfg['current_offset']} : {s1_cfg['current_offset'] + len(s1_new)}] of {s1_total}")
    print(f"    - Progress: {(min(s1_cfg['current_offset'] + len(s1_new), s1_total) / s1_total * 100):.1f}% of Stage 1")

    # 2. Stage 2 Slice (Account 3: mmossad2324)
    s2_new, s2_total = slice_file_lines(STAGE2_FULL, s2_cfg["current_offset"], s2_cfg["new_samples_per_chunk"])
    s2_cfg["total_samples"] = s2_total

    if len(s2_new) < s2_cfg["new_samples_per_chunk"]:
        remaining_needed = s2_cfg["new_samples_per_chunk"] - len(s2_new)
        wrap_slice, _ = slice_file_lines(STAGE2_FULL, 0, remaining_needed)
        s2_new.extend(wrap_slice)
        s2_cfg["is_completed"] = True
        print(f"[!] Stage 2 reached full coverage! Wrapping into next epoch review.")

    s2_replay = load_replay_samples(s2_cfg["replay_size"], seed=s2_cfg["completed_cycles"] + 200)
    s2_final = s2_new + s2_replay
    random.shuffle(s2_final)

    with open(STAGE2_ACTIVE_CHUNK, "w", encoding="utf-8") as f:
        for item in s2_final:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")

    print(f"[✓] Stage 2 Chunk Prepared: {len(s2_final)} samples ({len(s2_new)} fresh + {len(s2_replay)} replay)")
    print(f"    - Current Range: [{s2_cfg['current_offset']} : {s2_cfg['current_offset'] + len(s2_new)}] of {s2_total}")
    print(f"    - Progress: {(min(s2_cfg['current_offset'] + len(s2_new), s2_total) / s2_total * 100):.1f}% of Stage 2")

    save_cursor(cursor)
    print(f"{'='*75}\n")
    return cursor

def advance_cursor():
    """Advances the conveyor offsets after successful completion of training cycle."""
    cursor = load_cursor()
    s1 = cursor["stage1"]
    s2 = cursor["stage2"]

    s1["current_offset"] = (s1["current_offset"] + s1["new_samples_per_chunk"]) % s1["total_samples"]
    s1["completed_cycles"] += 1

    s2["current_offset"] = (s2["current_offset"] + s2["new_samples_per_chunk"]) % s2["total_samples"]
    s2["completed_cycles"] += 1

    if s1["is_completed"] and s2["is_completed"]:
        cursor["overall_epoch"] += 1
        print(f"\n🎉 [MILESTONE] FULL 27,000 SAMPLES DIGESTED! Advancing to Epoch {cursor['overall_epoch']} / Next Tier Sources!")

    save_cursor(cursor)
    print(f"[✓] Cursor advanced! Ready for Cycle {s1['completed_cycles'] + 1}.")
    return cursor

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "advance":
        advance_cursor()
    else:
        prepare_active_chunks()
