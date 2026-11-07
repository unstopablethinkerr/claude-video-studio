#!/usr/bin/env python3
"""List your Jarvis Labs instances, including ones you created by hand in the dashboard.

Usage:
  python3 scripts/find-instance.py            # list all instances
  python3 scripts/find-instance.py 123456     # check one instance by machine ID

Read-only. It never creates, resumes, pauses, or destroys anything.
Exit codes: 0 = found, 1 = not found, 2 = could not read data from the CLI.
"""
import json
import subprocess
import sys


def parse_json_loose(text: str):
    starts = [i for i in (text.find("["), text.find("{")) if i != -1]
    if not starts:
        raise ValueError("no JSON in output")
    return json.loads(text[min(starts):])


def list_instances():
    p = subprocess.run(["jl", "list", "--json"], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError((p.stderr or p.stdout).strip()[:300])
    data = parse_json_loose(p.stdout)
    if isinstance(data, dict):
        data = data.get("instances", [])
    return data


def describe(inst):
    status = str(inst.get("status", "unknown"))
    if status.lower() == "running":
        hint = "ready: Claude can continue work on it"
    elif status.lower() == "paused":
        hint = "paused: resuming starts billing for compute again"
    else:
        hint = "unusual status: check it in the Jarvis dashboard before using it"
    return (
        f"machine_id: {inst.get('machine_id')}\n"
        f"  name:      {inst.get('name') or '(no name)'}\n"
        f"  status:    {status}  ({hint})\n"
        f"  gpu:       {inst.get('gpu_type')} x{inst.get('num_gpus') or 1}  region {inst.get('region') or '?'}\n"
        f"  cost so far: {inst.get('cost')}"
    )


def main():
    try:
        instances = list_instances()
    except (RuntimeError, ValueError, FileNotFoundError) as e:
        print(f"Could not read instances: {e}")
        print("Run `jl setup` or check that `jl` is on your PATH.")
        return 2

    if len(sys.argv) == 2:
        wanted = sys.argv[1].strip()
        match = [i for i in instances if str(i.get("machine_id")) == wanted]
        if not match:
            print(f"No instance with machine_id {wanted} in this account.")
            return 1
        print(describe(match[0]))
        return 0

    if not instances:
        print("No instances in this account. Create one in the Jarvis dashboard or with `jl create`.")
        return 1
    for inst in instances:
        print(describe(inst))
        print()
    print("Pick a machine_id and set it as \"machine_id\" in jobs/job.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
