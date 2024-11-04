#!/usr/bin/env python3
"""Download public data and build data/manifest.json for a real-recording benchmark.

Speech: LibriSpeech test-clean (CC BY 4.0), ONE utterance per speaker (strict speaker independence).
Noise : DEMAND (CC BY 4.0, Zenodo 1227121), channel 1 of four environments.

Noise category labels describe the actual DEMAND environment:
    STRAFFIC -> traffic   PCAFETER -> babble   DKITCHEN -> household   OOFFICE -> office

Usage:  python scripts/build_real_manifest.py [--speakers 40] [--min-seconds 4.5]
Downloads about 0.35 GB (speech) + 0.4 GB (noise) into data/ (git-ignored).
"""
from __future__ import annotations

import argparse
import json
import tarfile
import urllib.request
import zipfile
from pathlib import Path

import soundfile as sf

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SPEECH_URL = "https://www.openslr.org/resources/12/test-clean.tar.gz"
NOISE_URL = "https://zenodo.org/records/1227121/files/{}_16k.zip"
NOISE = {"STRAFFIC": "traffic", "PCAFETER": "babble", "DKITCHEN": "household", "OOFFICE": "office"}


def fetch(url: str, dest: Path) -> None:
    if not dest.exists():
        dest.parent.mkdir(parents=True, exist_ok=True)
        print(f"downloading {url}", flush=True)
        urllib.request.urlretrieve(url, dest)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--speakers", type=int, default=40)
    ap.add_argument("--min-seconds", type=float, default=4.5)
    args = ap.parse_args()

    archive = DATA / "raw" / "test-clean.tar.gz"
    fetch(SPEECH_URL, archive)
    with tarfile.open(archive) as tar:
        tar.extractall(DATA / "raw", filter="data")
    speech_root = DATA / "raw" / "LibriSpeech" / "test-clean"

    noise_dir = DATA / "noise"
    noise_dir.mkdir(parents=True, exist_ok=True)
    for name in NOISE:
        zpath = DATA / "raw" / f"{name}_16k.zip"
        fetch(NOISE_URL.format(name), zpath)
        with zipfile.ZipFile(zpath) as z:
            member = next(m for m in z.namelist() if m.endswith("ch01.wav"))
            (noise_dir / f"{name}.wav").write_bytes(z.read(member))

    categories = list(NOISE.items())
    recordings = []
    for spk_dir in sorted(p for p in speech_root.iterdir() if p.is_dir()):
        if len(recordings) >= args.speakers:
            break
        pick = next((f for f in sorted(spk_dir.rglob("*.flac")) if sf.info(f).duration >= args.min_seconds), None)
        if pick is None:
            continue
        env, label = categories[len(recordings) % len(categories)]  # deterministic round-robin
        rel = pick.relative_to(DATA)
        recordings.append({
            "id": f"spk{spk_dir.name}_{label}",
            "clean": rel.as_posix(),
            "noise": f"noise/{env}.wav",
            "noise_category": label,
            "clean_source": "https://www.openslr.org/12/",
            "noise_source": "https://zenodo.org/records/1227121",
            "clean_license": "CC BY 4.0",
            "noise_license": "CC BY 4.0",
        })

    manifest = {"kind": "real_recordings", "recordings": recordings}
    (DATA / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"wrote {DATA / 'manifest.json'} with {len(recordings)} recordings")


if __name__ == "__main__":
    main()
