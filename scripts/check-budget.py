#!/usr/bin/env python3
"""Pre-flight budget check before ANY billable Jarvis Labs action.

Usage:  python3 scripts/check-budget.py jobs/job.json

Two modes, chosen by the job file:
  * New instance: leave "machine_id" empty. Prices the GPU from `jl gpus`,
    requires a free GPU, and checks the wallet against the full job cost.
  * Existing instance: set "machine_id" (for example, one created by hand
    in the Jarvis dashboard). Uses that instance's GPU, skips the free-GPU
    check, and checks the wallet against the job cost.

Exit codes:
  0  enough balance; go ahead after the user confirms in chat
  1  blocked (not enough balance, no capacity, over the hour cap, or unknown instance)
  2  could not read data from the CLI (ask the user to run `jl setup` or `jl status`)

Storage and idle time are billed separately by Jarvis Labs, so the safety
margin covers them. This script cannot set a spend limit on the account.
"""
import json
import subprocess
import sys
from pathlib import Path

SAFETY_MARGIN = 0.20  # 20 percent headroom for storage, idle time, and price changes


def parse_json_loose(text: str):
    """jl may print a one-line update banner before the JSON. Skip anything before the first bracket."""
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        raise ValueError("no JSON in output")
    return json.loads(text[min(starts):])


def run_jl(args):
    p = subprocess.run(["jl", *args, "--json"], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"`jl {' '.join(args)}` failed: {(p.stderr or p.stdout).strip()[:300]}")
    return parse_json_loose(p.stdout)


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    job_path = Path(sys.argv[1])
    if not job_path.exists():
        print(f"Job file not found: {job_path}. Copy jobs/job.example.json to jobs/job.json and fill it in.")
        return 2
    job = json.loads(job_path.read_text(encoding="utf-8"))

    try:
        status = run_jl(["status"])
        gpus = run_jl(["gpus"])
        instances = run_jl(["list"])
    except (RuntimeError, ValueError, FileNotFoundError) as e:
        print(f"Could not read Jarvis Labs data: {e}")
        print("Run `jl setup` (or check that `jl` is on your PATH), then try again.")
        return 2

    if isinstance(gpus, dict):
        gpus = gpus.get("gpus", [])
    if isinstance(instances, dict):
        instances = instances.get("instances", [])

    balance = float(status.get("balance", {}).get("balance", 0.0))
    grants = float(status.get("balance", {}).get("grants", 0.0))

    num_gpus = int(job.get("num_gpus", 1) or 1)
    target_videos = float(job.get("target_videos", 0))
    hours_per_video = float(job.get("hours_per_video", 0))
    max_hours = float(job.get("max_hours", 0))
    hours_total = target_videos * hours_per_video
    machine_id = str(job.get("machine_id") or "").strip()

    if machine_id:
        inst = next((i for i in instances if str(i.get("machine_id")) == machine_id), None)
        if inst is None:
            print(f"BLOCKED: machine_id {machine_id} is not in this account. Run scripts/find-instance.py to see yours.")
            return 1
        gpu_type = str(inst.get("gpu_type", "")).upper()
        num_gpus = int(inst.get("num_gpus") or num_gpus)
        region = str(inst.get("region", "") or "").upper()
        inst_status = str(inst.get("status", "unknown"))
        matches = [
            g for g in gpus
            if str(g.get("gpu_type", "")).upper() == gpu_type
            and (not region or str(g.get("region", "")).upper() == region)
            and g.get("price_per_hour") is not None
        ]
        if not matches:
            print(f"BLOCKED: no current price found for {gpu_type} in {region or 'any region'}. Check `jl gpus`.")
            return 1
        best = min(matches, key=lambda g: float(g["price_per_hour"]))
        price = float(best["price_per_hour"])
        mode_line = f"Existing instance {machine_id} ({inst.get('name') or 'no name'}), status: {inst_status}"
        free_line = "free-GPU check skipped, instance already allocated"
        free_ok = True
    else:
        gpu_type = str(job.get("gpu_type", "")).upper()
        region = str(job.get("region", "") or "").upper()
        matches = [
            g for g in gpus
            if str(g.get("gpu_type", "")).upper() == gpu_type
            and (not region or str(g.get("region", "")).upper() == region)
            and g.get("price_per_hour") is not None
        ]
        if not matches:
            print(f"BLOCKED: no price found for GPU '{gpu_type}'" + (f" in region '{region}'" if region else "") + ".")
            print("Run `jl gpus` to see what is available.")
            return 1
        best = min(matches, key=lambda g: float(g["price_per_hour"]))
        price = float(best["price_per_hour"])
        free = int(best.get("num_free_devices", 0) or 0)
        mode_line = "New instance (will be created)"
        free_line = f"free now: {free}"
        free_ok = free >= num_gpus

    compute_cost = price * num_gpus * hours_total
    required = compute_cost * (1 + SAFETY_MARGIN)

    print("=== Budget check ===")
    print(f"Mode:               {mode_line}")
    print(f"Project:            {job.get('project', '(unnamed)')}")
    print(f"Target videos:      {target_videos:g}  x  {hours_per_video:g} h each = {hours_total:g} h total")
    print(f"GPU:                {best.get('gpu_type')} x{num_gpus}  in {best.get('region', '?')}  at {price:.2f}/h ({free_line})")
    print(f"Estimated compute:  {compute_cost:.2f}")
    print(f"Required (+{int(SAFETY_MARGIN*100)}% margin): {required:.2f}")
    print(f"Wallet balance:     {balance:.2f}   (grants: {grants:.2f}, not counted)")
    print(f"Storage and idle time are billed separately.")

    if max_hours and hours_total > max_hours:
        print(f"BLOCKED: {hours_total:g} h is over max_hours ({max_hours:g}). Raise max_hours in the job file to confirm.")
        return 1
    if not free_ok:
        print(f"BLOCKED: only {free} free GPU(s) right now, job needs {num_gpus}. Try later or another region.")
        return 1
    if balance < required:
        print(f"BLOCKED: balance {balance:.2f} is below the required {required:.2f}. Top up or reduce the job.")
        return 1

    if machine_id and inst_status.lower() == "paused":
        print("NOTE: this instance is paused. Resuming starts compute billing again.")
    print("OK: balance covers this job. Confirm in chat before creating, resuming, or running on any instance.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
