#!/usr/bin/env python3
"""Transcribe media with faster-whisper (large-v3-turbo).

Usage:
  python3 scripts/transcribe.py raws/clip1.mp4     # one file
  python3 scripts/transcribe.py raws/              # every media file in a folder
Writes <name>.srt and <name>.json to --out (default: outputs/).
Uses CUDA when available, otherwise CPU with int8 (slower but works on laptops).
HyperFrames also has its own built-in: npx --yes hyperframes@0.9.19 transcribe <file>
"""
import argparse
import json
import sys
from pathlib import Path

MEDIA_EXT = {".mp4", ".mov", ".mkv", ".wav", ".mp3", ".m4a"}


def fmt_ts(sec: float) -> str:
    h, rem = divmod(sec, 3600)
    m, s = divmod(rem, 60)
    return f"{int(h):02d}:{int(m):02d}:{s:06.3f}".replace(".", ",")


def transcribe_file(model, path: Path, out_dir: Path, language):
    segments, info = model.transcribe(str(path), vad_filter=True, language=language)
    segs = list(segments)
    out_dir.mkdir(parents=True, exist_ok=True)

    srt_lines = []
    for i, seg in enumerate(segs, 1):
        srt_lines += [str(i), f"{fmt_ts(seg.start)} --> {fmt_ts(seg.end)}", seg.text.strip(), ""]
    (out_dir / f"{path.stem}.srt").write_text("\n".join(srt_lines), encoding="utf-8")

    data = {
        "file": path.name,
        "language": info.language,
        "segments": [{"start": s.start, "end": s.end, "text": s.text.strip()} for s in segs],
    }
    (out_dir / f"{path.stem}.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"done: {path.name} ({len(segs)} segments, lang={info.language})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("target")
    ap.add_argument("--out", default="outputs")
    ap.add_argument("--model", default="large-v3-turbo")
    ap.add_argument("--language", default=None, help="e.g. en, ta, hi. Auto-detect if omitted.")
    args = ap.parse_args()

    try:
        from faster_whisper import WhisperModel
    except ImportError:
        sys.exit("faster-whisper is not installed. Run: pip install faster-whisper")

    try:
        model = WhisperModel(args.model, device="cuda", compute_type="float16")
        print("Using GPU (CUDA)")
    except Exception:
        model = WhisperModel(args.model, device="cpu", compute_type="int8")
        print("Using CPU (int8). This is slower.")

    target = Path(args.target)
    if target.is_file():
        files = [target]
    elif target.is_dir():
        files = sorted(p for p in target.iterdir() if p.suffix.lower() in MEDIA_EXT)
    else:
        sys.exit(f"Not found: {target}")
    if not files:
        print("No media files found.")
        return
    for f in files:
        transcribe_file(model, f, Path(args.out), args.language)


if __name__ == "__main__":
    main()
