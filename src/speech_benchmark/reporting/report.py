"""Research-style Markdown report generated from measured results, never assumed rankings."""
import json
from pathlib import Path
import numpy as np
import pandas as pd
from speech_benchmark.metrics.aggregation import summarize
from .tables import write_tables
from .plots import generate_plots


def _md_table(df, columns, rounding=4):
    if df.empty:
        return "No valid measurements."
    data = df[columns].copy()
    for name in data.select_dtypes(include=["number"]).columns:
        data[name] = data[name].map(lambda x: f"{x:.{rounding}f}" if pd.notna(x) else "N/A")
    header = "| " + " | ".join(columns) + " |"
    divider = "|" + "|".join(["---"] * len(columns)) + "|"
    return "\n".join([header, divider] + ["| " + " | ".join(map(str, row)) + " |"
                                                   for row in data.itertuples(index=False, name=None)])


def generate_report(results_path: str | Path) -> Path:
    path = Path(results_path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"No result file: {path}")
    folder = path.parent
    metadata_path = folder / "run_metadata.json"
    if not metadata_path.is_file():
        raise FileNotFoundError("Missing run_metadata.json; cannot establish provenance")
    meta = json.loads(metadata_path.read_text(encoding="utf-8"))
    df = pd.read_csv(path)
    required = {"algorithm", "recording_id", "noise_category", "target_snr_db", "pesq",
                "stoi", "snr_improvement_db", "reconstruction_snr_db", "status"}
    if df.empty or not required.issubset(df):
        raise ValueError("Invalid or empty evaluation CSV")
    if not (df.status != "algorithm_failed").any():
        raise ValueError("No successful enhancement rows")
    stats = write_tables(df, folder, iterations=int(meta["metrics"].get("bootstrap_iterations", 2000)),
                         confidence=float(meta["metrics"].get("confidence_level", .95)))
    plots = generate_plots(df, folder / "figures", meta)
    summary = summarize(df)
    real = meta["manifest_kind"] == "real_recordings"
    quality = [m for m in ("pesq", "stoi", "reconstruction_snr_db", "snr_improvement_db")]
    count_pesq = df.pesq.notna().sum()
    count_stoi = df.stoi.notna().sum()
    winners = []
    for metric in quality:
        good = df.dropna(subset=[metric])
        if good.empty:
            winners.append(f"- **{metric}:** unavailable (no valid scores).")
            continue
        overall = good.groupby("algorithm")[metric].mean().sort_values(ascending=False)
        best, value = overall.index[0], overall.iloc[0]
        winners.append(f"- **{metric}:** observed largest unadjusted mean: `{best}` ({value:.4f}, "
                       f"{len(good[good.algorithm == best])} scored cases). This is not a "
                       "statistical superiority claim.")
    condition_lines = []
    for (category, snr), group in df.groupby(["noise_category", "target_snr_db"], sort=True):
        pairs = []
        for metric in ("pesq", "stoi", "snr_improvement_db"):
            good = group.dropna(subset=[metric])
            if good.empty:
                pairs.append(f"{metric}: N/A")
            else:
                avg = good.groupby("algorithm")[metric].mean().sort_values(ascending=False)
                pairs.append(f"{metric}: {avg.index[0]} ({avg.iloc[0]:.3f})")
        condition_lines.append(f"| {category} | {snr:g} | " + " | ".join(pairs) + " |")
    condition_header = ("| Noise | Target SNR (dB) | Largest PESQ mean | Largest STOI mean | "
                        "Largest Δ reconstruction SNR |\n|---|---:|---|---|---|")
    fig_lines = "\n".join(f"![{name}](figures/{name})" for name in plots)
    if not real:
        qualifier = ("**This run uses generated synthetic test signals rather than real speech. "
                     "The rankings below reflect software behaviour, not measured speech quality "
                     "or intelligibility.**")
    else:
        qualifier = ("**REAL-RECORDING EXPERIMENT:** Manifest labels state audio provenance; "
                     "objective metrics alone are not a listening study.")
    metric_explain = ("PESQ: aligned clean-to-degraded comparison via `pesq` binding; wideband "
                      "16 kHz or narrowband 8 kHz. STOI: `pystoi.stoi` with the same time "
                      "index, not a comprehension guarantee. SNR: 10 log10(mean(clean²) / "
                      "max(mean((clean−estimate)²),1e−12)); this **reconstruction** definition "
                      "penalizes speech distortion as well as noise. For synthetic mixtures, "
                      "input mixture SNR coincides with baseline reconstruction SNR because "
                      "noise is known. ΔSNR subtracts the noisy baseline per case. No "
                      "align-to-best-score operation or RMS normalization of denoiser outputs.")
    pinfo = (f"PESQ valid {count_pesq}/{len(df)}; STOI valid {count_stoi}/{len(df)}; "
             f"algorithm failures {(df.status == 'algorithm_failed').sum()}; "
             f"metric-partial rows {(df.status == 'metric_partial').sum()}.")
    text = f"""# Speech Enhancement Evaluation Benchmark: A Comparative Study of Speech Denoising Algorithms

## Abstract

{qualifier}

A paired, controlled multi-SNR benchmark executed {len(df)} algorithm/case evaluations over
{df.recording_id.nunique()} distinct recording identifiers and {df.case_id.nunique()} mixture cases.
{pinfo} The analysis compares a noisy control with spectral subtraction, smoothed spectral
gating and an STFT-domain Wiener filter; unavailable metrics are **missing**, not zeros.

## Introduction and problem statement

Speech enhancement trades environmental-noise attenuation against loss of speech components.
A filter that maximizes reconstruction SNR can worsen perceptual quality or intelligibility.
The task is to quantify the dependence of each method on noise content and mixture SNR.

## Research questions

1. Which method has the highest measured PESQ under each condition?
2. Which preserves estimated intelligibility (STOI)?
3. Which increases *reference-relative reconstruction SNR* most?
4. How do noise category and input SNR modify comparisons?
5. How much computation does each algorithm require?
6. Are paired differences consistent across independent recordings?

## Background and methods

A Hann-window STFT transforms overlapping frames into complex bins; processing magnitudes or
complex gains preserves mixture phase and an overlap-add inverse produces time-domain audio.
All methods have zero-lag output length. Spectral subtraction subtracts an estimated noise
magnitude and clamps gain at a configurable floor; narrow residual peaks can cause musical
noise, while large subtraction strengths attenuate speech harmonics. Spectral gating forms
a soft threshold mask and Gaussian-smooths time/frequency bins; profile mismatch can cause
pump artifacts or attenuate weak consonants. The Wiener estimator uses smoothed local
observed power minus the noise power (floored at zero), then applies gain
`P_s_hat/(P_s_hat+P_v_hat)`; this approximates linear MMSE under uncorrelated speech/noise
and locally stationary spectra, not a learned prior. Its performance is sensitive to PSD
estimation, and none of these methods guarantees perfect intelligibility.

## Dataset and controlled setup

- Manifest type: `{meta['manifest_kind']}`; recording IDs: {df.recording_id.nunique()}
- Configuration SHA256: `{meta['config_sha256']}`
- Manifest SHA256: `{meta['manifest_sha256']}`
- Sample rate: {meta['sample_rate']} Hz; segment length: {meta['segment_seconds']} s
- Target SNR values: {meta['snrs_db']}; random seed: {meta['seed']}
- Noise profile: `{meta['noise_profile']}`; profiles shared across methods.
- Algorithms: {meta['algorithms']}
- Alignment: {meta['alignment']}
- Processing-time measurement: {meta['timing']}
- Every input mixture is immutable to the individual denoisers; waveform export is 32-bit float.
- Audio hashes and licensing metadata: `run_metadata.json`.

## Objective metric definitions

{metric_explain}

STOI is not a human comprehension test; PESQ (P.862/P.862.2) is a legacy metric, withdrawn
by ITU in 2024 in favor of the P.863 family. PESQ code has separate IP/license restrictions;
see `docs/metrics.md`. Scores from different PESQ modes must not be pooled.

## Overall results

{_md_table(summary, [x for x in ('algorithm', 'total_cases', 'unique_recordings',
'pesq_mean','pesq_n','pesq_failures','stoi_mean','stoi_n','stoi_failures',
'reconstruction_snr_db_mean','snr_improvement_db_mean','processing_ms_mean') if x in summary])}

### Highest observed means (descriptive, not proven winners)

{chr(10).join(winners)}

## Conditional comparisons

{condition_header}
{chr(10).join(condition_lines)}

## Paired statistical analysis

Recording is the independent cluster. A pair compares identical input cases and first averages
within each recording, preventing SNR variants of the same utterance from being counted as
independent. With ≥3 recordings, a recording-level bootstrap provides percentile confidence
intervals; with ≥6 nonzero paired recordings, two-sided Wilcoxon signed-rank p-values are
calculated and Holm-corrected across the reported comparison family. Missing data are
excluded *pairwise*. These tests are exploratory with small or heterogeneous samples.

{_md_table(stats, [c for c in ('metric', 'baseline', 'alternative', 'paired_cases',
'independent_recordings', 'mean_difference', 'ci_low', 'ci_high', 'cohen_dz',
'wilcoxon_p', 'holm_p') if c in stats])}

## Figures and waveform/spectrogram examples

{fig_lines if fig_lines else 'No figures had sufficient valid data.'}

## Discussion, trade-offs, and limitations

Observed mean leaders are descriptive, not proofs of overall superiority. Classical denoisers
may improve reconstruction SNR while suppressing low-energy consonants, changing PESQ and
STOI in different directions. Comparisons are conditional on this selected recording set,
noise PSD profile, one hyperparameter configuration per method, signal segment length,
STFT settings and PESQ/STOI properties. Oracle PSD uses independent *known noise* in synthetic
mixing; this information is unavailable for most live applications, so use blind PSD to test
realistic deployment performance. Processing time excludes resampling, I/O, scoring and
warm-up, and is platform-specific, not end-to-end streaming latency. Real-world study needs
multiple speakers, independent noise recordings, profile mismatch experiments, listener
ratings and pre-registered method selection; error rates and missing scores must be inspected.

## Final evidence-based comparison

{qualifier}

Condition leaders above identify *measured maxima*, not a universal winner. Statistical
comparisons are shown only when justified by independent recording counts. Where PESQ is
missing, the PESQ-quality question is left open; synthetic runs describe software behaviour
rather than real-speech quality.

## References and licensing

- Panayotov et al., *LibriSpeech*, ICASSP 2015, CC BY 4.0: https://openslr.org/12/
- Thiemann et al., *DEMAND*, 2013, CC BY-SA 3.0: https://zenodo.org/records/1227121
- Reddy et al., *A Scalable Noisy Speech Dataset and Online Subjective Test Framework*, Interspeech 2019:
  https://github.com/microsoft/MS-SNSD
- ITU-T P.862 (withdrawn): https://www.itu.int/rec/T-REC-P.862
- Taal et al., *An Algorithm for Intelligibility Prediction of Time–Frequency Weighted Noisy Speech*,
  IEEE TASLP 2011 (STOI).
- Wiener, *Extrapolation, Interpolation, and Smoothing of Stationary Time Series*, 1949.
- This repository code uses MIT; dataset licenses and PESQ implementation/IP are **not**
  covered by the project MIT license.
"""
    destination = folder / "report.md"
    destination.write_text(text, encoding="utf-8")
    return destination
