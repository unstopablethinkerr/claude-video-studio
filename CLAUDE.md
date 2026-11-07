# Claude Video Studio: instructions for Claude

HyperFrames is pinned to version 0.9.19 everywhere. Always use `npx --yes hyperframes@0.9.19 <command>`.

## Layout
- `raws/` holds source footage. Never modify files here.
- `projects/<name>/` holds one HyperFrames composition (index.html plus assets). `projects/starter/` is a blank template to copy from.
- `outputs/` holds final renders and subtitle files.
- `jobs/job.json` holds the approved cloud job plan. It is personal and not committed.

## Workflow for a new video
1. Read the brief and list `raws/`.
2. Create a project if needed (non-interactive):
   `cd projects && npx --yes hyperframes@0.9.19 init <name> --non-interactive --example blank --skip-skills`
3. Captions, optional: `npx --yes hyperframes@0.9.19 transcribe raws/<file>` (built-in) or `python3 scripts/transcribe.py raws/<file>` (faster-whisper, GPU-friendly).
4. Edit `projects/<name>/index.html`. Prefer small, reviewable changes over rewrites. The user may type corrections and ideas right here in chat. Apply them as edits, then lint again.
5. Validate: `npx --yes hyperframes@0.9.19 lint projects/<name>` and `... inspect projects/<name>`. Fix errors and text overflow before rendering.
6. Preview (optional, interactive): `npx --yes hyperframes@0.9.19 preview projects/<name>`.
7. Render: `npx --yes hyperframes@0.9.19 render projects/<name> -o outputs/<name>.mp4`.

Local rendering needs a browser. If render fails with "Chrome not found", run `npx --yes hyperframes@0.9.19 browser ensure`. If that fails, the user installs Google Chrome and sets `HYPERFRAMES_BROWSER_PATH`.

## Cloud and money: read before any Jarvis Labs action

Jarvis Labs bills from the user's prepaid wallet. A running GPU bills per hour, including idle time. A paused instance still bills storage. A destroyed instance deletes its data.

You may manage the full instance lifecycle for the user (check, create, upload, run, download, pause) only under these rules:

1. **Plan first.** Read `jobs/job.json`. If it is missing, ask the user for: number of output videos, hours of GPU time per video, GPU type, number of GPUs, and a hard hour cap. Or ask them to fill the job form on the project's GitHub Pages guide and save the file.
2. **Check the budget.** Run `python3 scripts/check-budget.py jobs/job.json`. If the exit code is not 0, stop, report the reason, and do not create or resume anything. Exit 2 means the CLI data could not be read. Ask the user to run `jl setup` or `jl status`.
3. **Confirm in this chat.** Show the budget summary and wait for an explicit "yes" to this specific job. Earlier approvals and silence do not count. An approval for one job does not carry over to another.
4. **Stay inside the approved plan.** Do not change the GPU type, region, number of GPUs, or hour cap without asking. If the work will exceed `max_hours`, stop and ask.
5. **Prefer pause to destroy.** When the job finishes, run `jl pause <machine_id>`, then `jl list` to confirm nothing else is running. Tell the user the instance is paused and that storage still bills.
6. **Destroy only on explicit request.** Run `jl destroy` only when the user asks in this conversation. Warn first that all data on the instance is lost.
7. **Stop on balance errors.** If a command returns a 402 or 403 balance error, stop and tell the user to top up.
8. **Prefer local work for small jobs.** Suggest the cloud only when it saves real time, such as many videos or a slow machine.

Remote commands must use `jl exec <id> -- <command>`. The double dash is required.

## Continuing on an instance the user created by hand

Users can create and start an instance in the Jarvis dashboard, or with `jl create`, and then ask you to continue on it later. Treat that instance as a fallback, not as a new job.

1. **Find it.** Run `python3 scripts/find-instance.py` to list the account's instances. Use `python3 scripts/find-instance.py <machine_id>` to check one. This command is read-only.
2. **Never create a new instance while the user has one they want to use.** Ask which one, if there is more than one.
3. **Check the budget with the instance in the job file.** Set `"machine_id"` in `jobs/job.json` and run `python3 scripts/check-budget.py jobs/job.json`. The check uses the instance's own GPU and skips the free-GPU check.
4. **Running instance.** Confirm the plan in chat, then work on it with `jl exec` and `jl upload`/`jl download`. No resume needed.
5. **Paused instance.** Resuming starts compute billing again, so confirm first. Resume with `jl resume <machine_id>` and keep the same GPU. Never pass `--gpu`, `--num-gpus`, or `--storage` without asking, because each one changes the price or the plan.
6. **Anything else** (unusual status, no IP, or no response from `jl exec`): stop and ask the user to check the Jarvis dashboard.
7. **Finish the same way as any job.** Pause the instance when done and confirm with `jl list`. Destroy it only when the user asks.

## Rules
- Never print, commit, or paste API keys or tokens.
- If something fails and the cause is unclear, run `bash scripts/collect-debug.sh` and point the user to the zip it creates.
