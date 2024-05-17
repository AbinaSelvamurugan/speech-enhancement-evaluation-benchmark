"""Matplotlib batch figure generation. All plots use scored CSV input only."""
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import stft
from speech_benchmark.audio.loader import load_audio

LABEL = {
    "pesq": "PESQ MOS-LQO (higher better)",
    "stoi": "STOI estimate (higher better)",
    "reconstruction_snr_db": "Reconstruction SNR (dB)",
    "snr_improvement_db": "Reconstruction SNR improvement (dB)",
    "processing_ms": "Processing time (ms/clip)",
}


def _save(fig, folder, name):
    fig.tight_layout()
    fig.savefig(folder / f"{name}.png", dpi=180, bbox_inches="tight")
    # Vector pcolormesh expands into millions of path vertices; raster is better here.
    if name != "example_spectrograms":
        fig.savefig(folder / f"{name}.svg", bbox_inches="tight")
    plt.close(fig)


def generate_plots(df: pd.DataFrame, folder: Path, metadata: dict | None = None) -> list[str]:
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    files = []
    for metric in ("pesq", "stoi", "reconstruction_snr_db", "snr_improvement_db",
                   "processing_ms"):
        good = df.dropna(subset=[metric])
        if good.empty:
            continue
        summary = good.groupby("algorithm")[metric].agg(["mean", "count"]).sort_index()
        fig, ax = plt.subplots(figsize=(8, 4.7))
        bars = ax.bar(summary.index, summary["mean"])
        for bar, number in zip(bars, summary["count"]):
            ax.annotate(f"n={number}", (bar.get_x() + bar.get_width()/2, bar.get_height()),
                        xytext=(0, 4), textcoords="offset points", ha="center", fontsize=8)
        ax.set(ylabel=LABEL[metric], title=f"Measured mean {metric.replace('_',' ')}")
        ax.tick_params(axis="x", rotation=15)
        _save(fig, folder, f"mean_{metric}")
        files.append(f"mean_{metric}.png")
    for metric in ("pesq", "stoi", "snr_improvement_db"):
        good = df.dropna(subset=[metric])
        if good.empty:
            continue
        groups = [(name, g[metric].to_numpy()) for name, g in good.groupby("algorithm")]
        fig, ax = plt.subplots(figsize=(8, 4.7))
        ax.boxplot([g[1] for g in groups], tick_labels=[f"{k}\n(n={len(v)})" for k, v in groups])
        ax.set(ylabel=LABEL[metric], title=f"Per-case distribution: {metric}")
        _save(fig, folder, f"distribution_{metric}")
        files.append(f"distribution_{metric}.png")
        fig, ax = plt.subplots(figsize=(8, 4.7))
        for name, subgroup in good.groupby("algorithm"):
            means = subgroup.groupby("target_snr_db")[metric].agg(["mean", "count"])
            ax.plot(means.index, means["mean"], marker="o", label=f"{name} (n={len(subgroup)})")
        ax.set(xlabel="Configured input SNR (dB)", ylabel=LABEL[metric],
               title=f"{metric} versus mixture input SNR")
        ax.legend(fontsize=8)
        _save(fig, folder, f"versus_input_snr_{metric}")
        files.append(f"versus_input_snr_{metric}.png")
        means = good.pivot_table(index="noise_category", columns="algorithm",
                                 values=metric, aggfunc="mean")
        fig, ax = plt.subplots(figsize=(8, 4.7))
        means.plot.bar(ax=ax, rot=20)
        ax.set(xlabel="Noise recording category", ylabel=LABEL[metric],
               title=f"{metric} by noise category (means)")
        ax.legend(title="Algorithm", fontsize=8)
        _save(fig, folder, f"by_noise_{metric}")
        files.append(f"by_noise_{metric}.png")
    valid = df.dropna(subset=["pesq", "stoi"])
    if not valid.empty:
        fig, ax = plt.subplots(figsize=(7, 5))
        for name, subgroup in valid.groupby("algorithm"):
            ax.scatter(subgroup["stoi"], subgroup["pesq"], alpha=.45, label=f"{name} (n={len(subgroup)})")
        ax.set(xlabel=LABEL["stoi"], ylabel=LABEL["pesq"], title="Per-case quality/intelligibility")
        ax.legend(fontsize=8)
        _save(fig, folder, "pesq_stoi_tradeoff")
        files.append("pesq_stoi_tradeoff.png")
    if metadata:
        audio_root = folder.parent / "audio"
        for wav in sorted(audio_root.glob("*/clean.wav"))[:1]:
            other = wav.parent / "noisy.wav"
            enhanced = wav.parent / "wiener.wav"
            if not other.is_file() or not enhanced.is_file():
                continue
            audio = [load_audio(p)[0] for p in (wav, other, enhanced)]
            sr = int(metadata["sample_rate"])
            n = min(map(len, audio))
            labels = ["Clean reference", "Noisy mixture", "Wiener filtered"]
            fig, axes = plt.subplots(3, 1, figsize=(10, 6), sharex=True)
            for ax, item, label in zip(axes, audio, labels):
                ax.plot(np.arange(n)/sr, item[:n], linewidth=.35)
                ax.set(ylabel="Amplitude", title=label)
            axes[-1].set_xlabel("Time (s)")
            _save(fig, folder, "example_waveforms")
            files.append("example_waveforms.png")
            fig, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True)
            for ax, item, label in zip(axes, audio, labels):
                f, t, sp = stft(item[:n], sr, nperseg=512, noverlap=384)
                ax.pcolormesh(t, f, 20 * np.log10(np.maximum(np.abs(sp), 1e-6)),
                              shading="auto", cmap="viridis", vmin=-95, vmax=-20)
                ax.set(ylabel="Frequency (Hz)", title=label, ylim=(0, min(sr/2, 8000)))
            axes[-1].set_xlabel("Time (s); color = log magnitude (dB, common scale)")
            _save(fig, folder, "example_spectrograms")
            files.append("example_spectrograms.png")
    return files
