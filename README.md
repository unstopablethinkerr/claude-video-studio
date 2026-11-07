# Claude Video Studio

Edit and render videos by talking to Claude Code. Heavy work (Whisper transcription and HyperFrames rendering) can run on a rented GPU from [Jarvis Labs](https://jarvislabs.ai), so you don't need a powerful laptop.

![How Claude Video Studio works: raw footage, Claude Code, HyperFrames, Whisper, optional Jarvis GPU, MP4](docs/images/how-it-works.svg)

- **Editing engine:** [HyperFrames](https://github.com/heygen-com/hyperframes) (HeyGen, open source, Apache 2.0). You describe a video; Claude writes HTML/CSS/GSAP compositions; HyperFrames renders MP4.
- **Transcription:** `faster-whisper` with the `large-v3-turbo` model, for captions and subtitles.
- **Cloud bridge:** Jarvis Labs CLI (`jl`), linked to Claude Code through its agent skill.

Setup guide page: `index.html` (publish it with GitHub Pages).

## Quick start (local)

```bash
git clone https://github.com/unstopablethinkerr/claude-video-studio.git
cd claude-video-studio
bash scripts/setup-local.sh
claude            # open Claude Code in this folder
```

Inside Claude Code, ask for a video, for example:

> Create a 20-second product teaser in projects/teaser-1 using raws/clip1.mp4. Add captions from the transcript and render to outputs/teaser-1.mp4.

## Folder layout

| Folder | Purpose | In git? |
|---|---|---|
| `raws/` | Original footage and audio. Large. | No (ignored) |
| `projects/<name>/` | One HyperFrames composition per video | Yes |
| `outputs/` | Rendered MP4s and SRT files | No (ignored) |
| `scripts/` | Setup, upload, transcription, and cloud render scripts | Yes |
| `docs/` | Analysis and notes | Yes |

## Cloud workflow (for low-spec machines)

1. Create a Jarvis Labs account, add credit, and create an API key.
2. `jl setup` and paste the key. This also installs the Jarvis skill for Claude Code.
3. Create an instance: `jl create --gpu <GPU> --storage 100 --name video-studio`. Check GPUs and prices first with `jl gpus`.
4. Run the bulk job: `bash scripts/cloud-render.sh <machine_id>`. It uploads `raws/` and `projects/`, installs Node 22, ffmpeg, Chrome, and Whisper on the instance, transcribes everything, renders every project, and downloads `outputs/`.
5. Pause or destroy the instance when done. See the billing notes in `docs/ANALYSIS.md`.

## Test the setup

```bash
npx --yes hyperframes@0.9.19 lint projects/starter    # should report 0 errors
npx --yes hyperframes@0.9.19 render projects/starter -o outputs/starter.mp4
```

Rendering needs a browser. If it says "Chrome not found", run `npx --yes hyperframes@0.9.19 browser ensure`, or install Google Chrome and set `HYPERFRAMES_BROWSER_PATH`.

## Using an instance you created by hand

You can create an instance in the Jarvis dashboard (or with `jl create`), start it, and ask Claude Code to continue on it later as a fallback.

1. Run `python3 scripts/find-instance.py` to see your instances and their machine IDs.
2. Copy `jobs/job.example.json` to `jobs/job.json` and set `"machine_id"` to that ID.
3. Run `python3 scripts/check-budget.py jobs/job.json`, then confirm in Claude Code.

Claude will not create a second instance while you have one you want to use. If the instance is paused, resuming it starts billing again.

## Budget and cloud costs (read this first)

Jarvis Labs bills from your prepaid wallet. A GPU running for an hour costs that hour, even if it sits idle. A paused instance still bills storage, and a forgotten instance keeps running.

Before any cloud job:
1. Copy `jobs/job.example.json` to `jobs/job.json` and fill it in, or use the job form on the setup guide page.
2. Run `python3 scripts/check-budget.py jobs/job.json`. It reads your balance and GPU price, and blocks the job if the balance is too low or the hour cap is exceeded.
3. Confirm in the Claude Code chat before anything is created. Claude will pause the instance when the job finishes.

The CLI does not enforce a spending limit on your account. Check `jl list` and your Jarvis dashboard, and pause or destroy instances yourself if a session ends early. `jl destroy` deletes data.

## Something broke?

Run `bash scripts/collect-debug.sh`. It creates `debug-report.zip` with versions and diagnostics, with tokens redacted. Share that zip. Test results and known limits are in `docs/TESTING.md`.

## Secrets

Never commit API keys. `.env` is ignored. Copy `.env.example` to `.env` if you use `JL_API_KEY` directly.

## Maintainer

This repo is maintained by **Bala Santhosh**.

- Instagram: [@unstopablethinker](https://instagram.com/unstopablethinker)
- LinkedIn: [linkedin.com/in/bala-santhoshb](https://www.linkedin.com/in/bala-santhoshb)

Found a bug or have a question? Open an issue on this repo, or message on Instagram or LinkedIn.
