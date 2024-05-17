"""CLI entry point for the speech enhancement benchmark."""
import argparse
import importlib
import json
from pathlib import Path
import sys
import numpy as np
import matplotlib.pyplot as plt
from speech_benchmark.audio.loader import load_audio, save_audio
from speech_benchmark.audio.mixing import mix_at_snr, select_noise
from speech_benchmark.algorithms.base import EnhancementContext
from speech_benchmark.algorithms.registry import create, REGISTRY
from speech_benchmark.config import load_settings
from speech_benchmark.evaluation.experiments import read_manifest
from speech_benchmark.evaluation.runner import run_benchmark
from speech_benchmark.evaluation.audit import audit_results
from speech_benchmark.reporting.report import generate_report
from speech_benchmark.utils.reproducibility import rng_for


def _split(value: str):
    return [v.strip() for v in value.split(",") if v.strip()]


def _add_filters(p):
    p.add_argument("--config", default="configs/benchmark.yaml")
    p.add_argument("--snrs", help="Comma-separated dB values, e.g. -5,0,5; use --snrs=-5,0,5")
    p.add_argument("--categories", help="Comma-separated noise categories")
    p.add_argument("--algorithms", help="Comma-separated registered methods")
    p.add_argument("--max-recordings", type=int, default=None)


def _select(args, settings):
    snrs = [float(x) for x in _split(args.snrs)] if args.snrs else None
    categories = _split(args.categories) if args.categories else None
    algs = _split(args.algorithms) if args.algorithms else None
    if algs:
        for name in algs:
            create(name, settings.algorithm_options)
    return snrs, categories, algs


def _prepare(settings, args):
    records = read_manifest(settings.manifest)
    snrs, categories, _ = _select(args, settings)
    if categories:
        records = [r for r in records if r.noise_category in categories]
    if args.max_recordings is not None and args.max_recordings > 0:
        records = records[:args.max_recordings]
    if not records:
        raise ValueError("No recordings match requested filters")
    snrs = snrs if snrs is not None else settings.snrs_db
    out = settings.output_dir / "prepared"
    count = 0
    for record in records:
        clean, _ = load_audio(record.clean, settings.sample_rate)
        noise, _ = load_audio(record.noise, settings.sample_rate)
        clean = clean[:int(settings.segment_seconds * settings.sample_rate)]
        if len(clean) < settings.sample_rate:
            raise ValueError(f"Short recording {record.recording_id}")
        v = select_noise(noise, len(clean), rng_for(settings.seed, record.recording_id))
        for snr in snrs:
            s, y, _, _ = mix_at_snr(clean, v, snr, settings.metric_options["power_floor"])
            directory = out / f"{record.recording_id}__{snr:g}dB"
            save_audio(directory / "clean.wav", s, settings.sample_rate)
            save_audio(directory / "noisy.wav", y, settings.sample_rate)
            count += 1
    print(f"Prepared {count} mixture cases under {out}")


def main(argv=None):
    parser = argparse.ArgumentParser(prog="speech-benchmark",
            description="Paired speech/noise enhancement evaluation (PESQ, STOI, SNR)")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("doctor", help="Print dependency versions and availability")
    inspect = sub.add_parser("inspect", help="Inspect a real audio file's metadata")
    inspect.add_argument("file")
    inspect.add_argument("--plot", help="Save amplitude/spectrogram PNG")
    prepare = sub.add_parser("prepare", help="Generate controlled noisy mixtures")
    _add_filters(prepare)
    run = sub.add_parser("run", help="Benchmark all selected denoisers and metrics")
    _add_filters(run)
    one = sub.add_parser("enhance", help="Enhance one existing noisy audio file")
    one.add_argument("--input", required=True)
    one.add_argument("--output", required=True)
    one.add_argument("--algorithm", choices=list(REGISTRY), required=True)
    one.add_argument("--noise-reference", help="Independent pure-noise recording for oracle profile")
    one.add_argument("--config", default="configs/benchmark.yaml")
    report = sub.add_parser("report", help="Build tables, charts, research-style report")
    report.add_argument("--results", default="results/benchmark/benchmark.csv")
    audit = sub.add_parser("audit", help="Audit output integrity and SNR identities")
    audit.add_argument("--results", default="results/benchmark/benchmark.csv")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            versions = {}
            for name in ("numpy", "scipy", "soundfile", "pystoi", "pesq", "matplotlib",
                         "pandas", "yaml", "pytest", "ruff"):
                try:
                    package = importlib.import_module(name)
                    versions[name] = getattr(package, "__version__", "installed; version unknown")
                except Exception as exc:
                    versions[name] = f"UNAVAILABLE: {exc}"
            print(json.dumps({"python": sys.version.split()[0], "dependencies": versions,
                              "methods": list(REGISTRY), "pesq_supported":
                              "wb@16000 or nb@8000/16000; project enforces nb@8k, wb@16k"}, indent=2))
        elif args.command == "inspect":
            audio, sr = load_audio(args.file)
            info = {"file": args.file, "sample_rate": sr, "frames": len(audio),
                    "seconds": len(audio)/sr, "rms": float(np.sqrt(np.mean(audio**2))),
                    "peak": float(np.max(np.abs(audio)))}
            print(json.dumps(info, indent=2))
            if args.plot:
                fig, ax = plt.subplots(figsize=(10, 3))
                ax.plot(np.arange(len(audio))/sr, audio, lw=.4)
                ax.set(xlabel="Time (s)", ylabel="Amplitude")
                fig.tight_layout()
                Path(args.plot).parent.mkdir(parents=True, exist_ok=True)
                fig.savefig(args.plot, dpi=160)
                plt.close(fig)
                print(f"Saved {args.plot}")
        elif args.command in ("run", "prepare"):
            settings = load_settings(args.config)
            if args.command == "prepare":
                _prepare(settings, args)
            else:
                snrs, categories, algs = _select(args, settings)
                df = run_benchmark(settings, snrs=snrs, categories=categories,
                                    algorithms=algs, max_recordings=args.max_recordings)
                print(f"Wrote {len(df)} measured rows to {settings.output_dir / 'benchmark.csv'}")
                print("PESQ valid:", int(df.pesq.notna().sum()), "STOI valid:",
                      int(df.stoi.notna().sum()))
        elif args.command == "enhance":
            settings = load_settings(args.config)
            data, _ = load_audio(args.input, settings.sample_rate)
            ref = None
            if args.noise_reference:
                ref, _ = load_audio(args.noise_reference, settings.sample_rate)
            profile = "oracle" if ref is not None else "blind"
            method = create(args.algorithm, settings.algorithm_options)
            output = method.enhance(data, EnhancementContext(settings.sample_rate, ref, profile))
            save_audio(args.output, output, settings.sample_rate)
            print(f"Saved enhanced {args.algorithm} recording to {args.output}")
        elif args.command == "audit":
            print(json.dumps(audit_results(args.results), indent=2))
        elif args.command == "report":
            destination = generate_report(args.results)
            print(f"Report saved to {destination}")
    except (OSError, RuntimeError, ValueError, KeyError) as exc:
        parser.exit(2, f"ERROR: {type(exc).__name__}: {exc}\n")


if __name__ == "__main__":
    main()
