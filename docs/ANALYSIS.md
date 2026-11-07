# Analysis: Claude + HyperFrames video editing with Jarvis Labs

## 1. What is being combined

| Piece | Role | Notes |
|---|---|---|
| Claude Code | Agent that writes and edits the video composition | Needs a Claude subscription or API access |
| HyperFrames | Renders HTML/CSS/GSAP compositions to MP4, MOV, or WebM | Open source (Apache 2.0) by HeyGen, released April 2026. Node 22+ needed |
| faster-whisper (large-v3-turbo) | Speech-to-text for captions and timing | Much faster on a GPU than on a laptop CPU |
| Jarvis Labs CLI (`jl`) | Creates and controls rented GPU instances from the terminal | Install with `uv tool install jarvislabs`. `jl setup` can install a Claude Code skill |

The core idea: a video becomes code. Claude edits code, so a "change the caption on scene 3" request becomes a small, reviewable diff, not a timeline drag.

## 2. Why the cloud helps people with low-spec machines

Rendering and transcription are the two heavy steps.

- **Transcription** benefits most from a GPU. A 10-minute clip that takes a long time on a laptop CPU can finish much faster on a rented GPU.
- **Rendering** runs headless Chrome to capture frames, then encodes them with ffmpeg. Frame capture is CPU- and browser-bound, so a bigger instance helps with longer or heavier compositions. Benchmark this yourself on your first real project, because the speedup depends on the composition.
- **Storage** is the hidden cost. Raw footage is large. Keep raws on a Jarvis filesystem or your own drive, and upload only what each job needs.

## 3. Recommended workflow

1. **Author locally.** Use Claude Code on the laptop for writing and editing compositions. This is cheap because it's mostly text.
2. **Preview at low resolution locally** if the machine can handle it. If not, skip local preview.
3. **Batch on the cloud.** When it's time to transcribe or render many files, run `scripts/cloud-render.sh <machine_id>`. It uploads files, transcribes everything, renders every project, and downloads the outputs.
4. **Stop billing.** Use `jl pause` between sessions to stop compute billing. Use `jl destroy` only when you're sure you're done, because it deletes the instance's data.

## 4. Cost and billing (verify before you commit)

- Pricing and availability change. Check live numbers with `jl gpus` (price per hour, free devices by region).
- Compute and storage are billed separately. Pausing stops compute, but retained storage still costs money.
- Keep a spending limit in mind. Check `jl status` before a big job.
- A bulk render that runs unattended can cost more than expected. Start with one short project to measure time and cost, then scale up.

## 5. Risks and limitations

- **HyperFrames is new.** It launched in April 2026, so expect rough edges and fast changes. Pin versions in `projects/` when a video is final.
- **Quality depends on the prompt and the composition.** Claude can produce working but plain layouts. Iterate with specific instructions, such as "move the title to the lower third and use a 0.4s fade."
- **Jarvis CLI docs are still being revised.** Flags in `scripts/` were written from current docs and may change. Run `jl <command> --help` to confirm before a large job. `jl exec` and the render loop in `cloud-render.sh` are the most likely places to need adjustment.
- **Audio language.** Whisper handles many languages, including Tamil and Hindi. Set `--language` when you know the language, because auto-detect can be wrong on short or mixed-language clips.
- **Privacy.** Footage uploaded to a cloud instance leaves your machine. Don't upload private or client material you're not allowed to share.
- **Secrets.** The API key must never be committed. `.env` and `*.key` are ignored by `.gitignore`.

## 6. Setup order (summary)

1. Install Node 22+, then run `bash scripts/setup-local.sh`.
2. Create a Jarvis Labs account, add funds, and create an API token.
3. Run `jl setup`, paste the token, and choose Claude Code.
4. Confirm with `jl status` and `jl gpus`.
5. Create an instance: `jl create --gpu <GPU> --storage 100 --name video-studio`.
6. Put footage in `raws/`, then run `bash scripts/cloud-render.sh <machine_id>` for batch jobs.
7. Publish `index.html` with GitHub Pages so others can follow the same steps.

## 7. Verdict

The combination is practical for people with modest laptops, as long as they accept the trade-offs above. The most valuable piece is the bulk pipeline: transcribe once on a GPU, render many projects in one session, and pause the instance afterward. Start small, measure time and cost on one video, and grow from there.

## 8. Alternatives and notes (added after testing)

- **HyperFrames cloud rendering.** `npx hyperframes cloud` renders on HeyGen's servers, so no local Chrome or ffmpeg is needed. It requires a HeyGen sign-in and is a separate paid service. Compare it with Jarvis Labs before choosing.
- **Built-in transcription.** HyperFrames has `transcribe`, which uses whisper-cpp or Parakeet and needs its own model install. `scripts/transcribe.py` uses faster-whisper on the GPU instance. Both are valid; the Jarvis route is better for many large files.
- **Browser requirement.** Local and cloud rendering both need Chrome Headless Shell (`hyperframes browser ensure`) or Google Chrome. This is the most common setup failure, so `setup-local.sh` and `docs/TESTING.md` cover it.
- **Pinning.** Everything uses HyperFrames 0.9.19. Upgrade only after one test render passes.
- **Telemetry.** HyperFrames collects anonymous usage data unless disabled with `hyperframes telemetry disable`.

## 9. Cost controls (added for the wallet model)

- The CLI bills from a prepaid wallet. `jl status` shows the balance, and an insufficient balance returns a 402 or 403 error.
- No account-wide spending limit is available from the CLI as far as I can tell. The controls in this repo are: a job file with an hour cap, a budget check that runs before any billable action, a 20 percent safety margin, and a rule that Claude must confirm in chat before creating or resuming anything.
- The biggest risk is an instance left running after a session ends. Pause at the end of every job and check `jl list`.
- Storage keeps billing while an instance is paused. Destroy an instance only when you are sure its data is backed up elsewhere.
