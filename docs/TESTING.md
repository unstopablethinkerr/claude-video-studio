# Testing report

What was tested, on which tools, and what still needs a real machine. Last run: 2026-11-07.

## Verified in a clean sandbox

| Check | Result |
|---|---|
| Jarvis CLI (`jarvislabs` 0.2.19) installs with `uv tool install` | Pass |
| `jl` command flags used in scripts (`create`, `exec`, `upload`, `download`, `get`, `pause`, `setup`, `status`, `gpus`) | Pass after fixes (see below) |
| HyperFrames 0.9.19 `init --non-interactive --example blank` | Pass |
| HyperFrames `lint` on the starter project | Pass: 0 errors, 0 warnings |
| HyperFrames `doctor` | Runs. Reports missing Chrome, Docker, and optional whisper-cpp, TTS, BGM |
| Bash syntax for all scripts (`bash -n`) | Pass |
| Python syntax and timestamp formatting in `transcribe.py` | Pass |
| `cloud-render.sh` command sequence, using a logging stub for `jl` | Pass after fixes |
| `setup-local.sh` end to end | Pass with warnings (Chrome cannot be downloaded in the sandbox) |
| `collect-debug.sh` produces a zip | Pass |

## Not verified here (needs a real machine)

- **Test render.** The sandbox cannot reach Google's storage, so Chrome Headless Shell could not be installed and no MP4 was rendered. A user must run one render on their own machine.
- **Whisper transcription.** Model download from Hugging Face is outside the sandbox's allowed domains. Test `scripts/transcribe.py` once.
- **Jarvis instance run.** No instance was created (that costs money). The remote commands were checked by reading the CLI source and with a stub, not against a live instance.
- **Chrome on the instance.** `remote-bootstrap.sh` installs Google Chrome from Google's apt repo. It assumes Ubuntu or Debian on x86_64 with root access.

## Bugs found and fixed during testing

1. `jl exec` needs `--` before the remote command. Without it the command is treated as one program name and fails.
2. `source` does not work under `sh`. Remote commands now run through `bash -c`.
3. `jl upload` and `jl download` treat an existing destination as a parent folder. Raws would have landed in `raws/raws/`, and outputs would have nested the same way. Uploads now target the parent folder, and outputs are packed into one archive for download.
4. The render loop captured `jl exec` output to build the project list, but the CLI also prints status lines to stdout. The loop now iterates over local folders.
5. `hyperframes render` takes a project directory, not `index.html`, and the output flag is `-o`.
6. A failed download no longer prints "Done". The script exits with a retry command.
7. Chrome was not installed on the instance, so renders would fail there. The bootstrap now installs it and sets `HYPERFRAMES_BROWSER_PATH`.

## Known limits

- Jarvis CLI docs are still being revised. Re-check `jl exec --help`, `jl upload --help`, and `jl download --help` if a command behaves differently.
- HyperFrames is new (April 2026) and pinned to 0.9.19. Upgrade only after a test render passes.
- HyperFrames collects anonymous usage data by default. Disable with `npx --yes hyperframes@0.9.19 telemetry disable`.

## Budget check (added later)

`scripts/check-budget.py` was tested against a stub `jl` that returns the JSON shapes read from the CLI source (`status` returns `balance.balance`, `gpus` returns a list with `gpu_type`, `region`, `price_per_hour`, `num_free_devices`). It also handles a version banner before the JSON.

| Case | Result |
|---|---|
| Balance 50, job needs 3.60 | Exit 0, OK |
| Balance 3, job needs 3.60 | Exit 1, blocked |
| 25 hours against a 6-hour cap | Exit 1, blocked |
| `jl` not on PATH | Exit 2, asks the user to run `jl setup` |

Not tested against a live account. The balance field name and GPU list format come from reading the CLI source, not from a real response. If the balance reads as zero on a real account, check `jl status --json` and report the output.

## Existing instances (added later)

`scripts/find-instance.py` and the existing-instance mode of `check-budget.py` were tested against a stub `jl list --json` with a running instance, a paused instance, and an unknown ID. Results:

| Case | Result |
|---|---|
| List instances | Pass: shows ID, name, status, GPU, region, cost |
| Look up a missing ID | Exit 1, "not in this account" |
| Running instance, enough balance | Exit 0, free-GPU check skipped |
| Paused instance, low balance | Exit 1, blocked; notes resume billing |
| Unknown machine_id in job file | Exit 1, blocked |
| New-instance mode still checks free GPUs | Exit 1 when none free |

Still untested against a live account: the real `status` values Jarvis returns. The scripts treat "running" and "paused" specially and show a warning for anything else.
