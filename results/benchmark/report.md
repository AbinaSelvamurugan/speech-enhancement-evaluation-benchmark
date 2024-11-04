# Speech Enhancement Evaluation Benchmark: A Comparative Study of Speech Denoising Algorithms

## Abstract

**REAL-RECORDING EXPERIMENT:** Manifest labels state audio provenance; objective metrics alone are not a listening study.

A paired, controlled multi-SNR benchmark executed 800 algorithm/case evaluations over
40 distinct recording identifiers and 200 mixture cases.
PESQ valid 800/800; STOI valid 800/800; algorithm failures 0; metric-partial rows 0. The analysis compares a noisy control with spectral subtraction, smoothed spectral
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

- Manifest type: `real_recordings`; recording IDs: 40
- Configuration SHA256: `fe6ed79ddc3d7cc06ffbc234e19bcb07275988c7903891196917a08e43fef366`
- Manifest SHA256: `502831e48bf7ce3a672e68440e3f6ffef5c7bd0bc367f69f4f8c9203d7a0ce04`
- Sample rate: 16000 Hz; segment length: 4.0 s
- Target SNR values: [-5.0, 0.0, 5.0, 10.0, 15.0]; random seed: 20240101
- Noise profile: `oracle`; profiles shared across methods.
- Algorithms: ['noisy', 'spectral_subtraction', 'spectral_gating', 'wiener']
- Alignment: zero-lag equal-length exact samples; no post hoc shifting
- Processing-time measurement: enhance() only; excludes loading, resampling, warmup, scoring, saving
- Every input mixture is immutable to the individual denoisers; waveform export is 32-bit float.
- Audio hashes and licensing metadata: `run_metadata.json`.

## Objective metric definitions

PESQ: aligned clean-to-degraded comparison via `pesq` binding; wideband 16 kHz or narrowband 8 kHz. STOI: `pystoi.stoi` with the same time index, not a comprehension guarantee. SNR: 10 log10(mean(clean²) / max(mean((clean−estimate)²),1e−12)); this **reconstruction** definition penalizes speech distortion as well as noise. For synthetic mixtures, input mixture SNR coincides with baseline reconstruction SNR because noise is known. ΔSNR subtracts the noisy baseline per case. No align-to-best-score operation or RMS normalization of denoiser outputs.

STOI is not a human comprehension test; PESQ (P.862/P.862.2) is a legacy metric, withdrawn
by ITU in 2024 in favor of the P.863 family. PESQ code has separate IP/license restrictions;
see `docs/metrics.md`. Scores from different PESQ modes must not be pooled.

## Overall results

| algorithm | total_cases | unique_recordings | pesq_mean | pesq_n | pesq_failures | stoi_mean | stoi_n | stoi_failures | reconstruction_snr_db_mean | snr_improvement_db_mean | processing_ms_mean |
|---|---|---|---|---|---|---|---|---|---|---|---|
| noisy | 200.0000 | 40.0000 | 1.7931 | 200.0000 | 0.0000 | 0.9051 | 200.0000 | 0.0000 | 5.0000 | 0.0000 | 0.1083 |
| spectral_gating | 200.0000 | 40.0000 | 2.2140 | 200.0000 | 0.0000 | 0.9057 | 200.0000 | 0.0000 | 10.1694 | 5.1694 | 20.4133 |
| spectral_subtraction | 200.0000 | 40.0000 | 2.2806 | 200.0000 | 0.0000 | 0.9044 | 200.0000 | 0.0000 | 12.7196 | 7.7196 | 17.6169 |
| wiener | 200.0000 | 40.0000 | 2.1071 | 200.0000 | 0.0000 | 0.9051 | 200.0000 | 0.0000 | 11.2798 | 6.2798 | 21.3788 |

### Highest observed means (descriptive, not proven winners)

- **pesq:** observed largest unadjusted mean: `spectral_subtraction` (2.2806, 200 scored cases). This is not a statistical superiority claim.
- **stoi:** observed largest unadjusted mean: `spectral_gating` (0.9057, 200 scored cases). This is not a statistical superiority claim.
- **reconstruction_snr_db:** observed largest unadjusted mean: `spectral_subtraction` (12.7196, 200 scored cases). This is not a statistical superiority claim.
- **snr_improvement_db:** observed largest unadjusted mean: `spectral_subtraction` (7.7196, 200 scored cases). This is not a statistical superiority claim.

## Conditional comparisons

| Noise | Target SNR (dB) | Largest PESQ mean | Largest STOI mean | Largest Δ reconstruction SNR |
|---|---:|---|---|---|
| babble | -5 | pesq: spectral_gating (1.057) | stoi: noisy (0.607) | snr_improvement_db: spectral_subtraction (6.941) |
| babble | 0 | pesq: spectral_subtraction (1.131) | stoi: noisy (0.721) | snr_improvement_db: spectral_subtraction (5.668) |
| babble | 5 | pesq: spectral_gating (1.329) | stoi: wiener (0.820) | snr_improvement_db: spectral_subtraction (4.401) |
| babble | 10 | pesq: spectral_gating (1.701) | stoi: wiener (0.892) | snr_improvement_db: wiener (3.223) |
| babble | 15 | pesq: spectral_gating (2.247) | stoi: wiener (0.934) | snr_improvement_db: wiener (2.422) |
| household | -5 | pesq: spectral_subtraction (1.363) | stoi: noisy (0.883) | snr_improvement_db: spectral_subtraction (10.131) |
| household | 0 | pesq: spectral_subtraction (1.727) | stoi: noisy (0.926) | snr_improvement_db: spectral_subtraction (9.775) |
| household | 5 | pesq: spectral_subtraction (2.246) | stoi: spectral_subtraction (0.956) | snr_improvement_db: spectral_subtraction (9.245) |
| household | 10 | pesq: spectral_subtraction (2.846) | stoi: noisy (0.975) | snr_improvement_db: spectral_subtraction (8.500) |
| household | 15 | pesq: spectral_subtraction (3.401) | stoi: noisy (0.987) | snr_improvement_db: spectral_subtraction (7.503) |
| office | -5 | pesq: spectral_subtraction (2.158) | stoi: spectral_subtraction (0.924) | snr_improvement_db: spectral_subtraction (10.943) |
| office | 0 | pesq: spectral_subtraction (2.749) | stoi: spectral_subtraction (0.958) | snr_improvement_db: spectral_subtraction (10.711) |
| office | 5 | pesq: spectral_subtraction (3.323) | stoi: spectral_subtraction (0.978) | snr_improvement_db: spectral_subtraction (10.258) |
| office | 10 | pesq: spectral_gating (3.852) | stoi: wiener (0.989) | snr_improvement_db: spectral_subtraction (9.462) |
| office | 15 | pesq: spectral_gating (4.194) | stoi: wiener (0.996) | snr_improvement_db: spectral_subtraction (8.279) |
| traffic | -5 | pesq: spectral_subtraction (1.225) | stoi: wiener (0.822) | snr_improvement_db: spectral_subtraction (9.632) |
| traffic | 0 | pesq: spectral_subtraction (1.502) | stoi: wiener (0.900) | snr_improvement_db: spectral_subtraction (8.567) |
| traffic | 5 | pesq: spectral_subtraction (1.951) | stoi: spectral_subtraction (0.947) | snr_improvement_db: spectral_subtraction (7.490) |
| traffic | 10 | pesq: spectral_subtraction (2.502) | stoi: wiener (0.972) | snr_improvement_db: spectral_subtraction (6.409) |
| traffic | 15 | pesq: spectral_subtraction (3.189) | stoi: spectral_subtraction (0.985) | snr_improvement_db: spectral_subtraction (5.314) |

## Paired statistical analysis

Recording is the independent cluster. A pair compares identical input cases and first averages
within each recording, preventing SNR variants of the same utterance from being counted as
independent. With ≥3 recordings, a recording-level bootstrap provides percentile confidence
intervals; with ≥6 nonzero paired recordings, two-sided Wilcoxon signed-rank p-values are
calculated and Holm-corrected across the reported comparison family. Missing data are
excluded *pairwise*. These tests are exploratory with small or heterogeneous samples.

| metric | baseline | alternative | paired_cases | independent_recordings | mean_difference | ci_low | ci_high | cohen_dz | wilcoxon_p | holm_p |
|---|---|---|---|---|---|---|---|---|---|---|
| pesq | noisy | spectral_gating | 200.0000 | 40.0000 | 0.4210 | 0.3454 | 0.5072 | 1.5859 | 0.0000 | 0.0000 |
| pesq | noisy | spectral_subtraction | 200.0000 | 40.0000 | 0.4876 | 0.3961 | 0.5860 | 1.5767 | 0.0000 | 0.0000 |
| pesq | noisy | wiener | 200.0000 | 40.0000 | 0.3140 | 0.2194 | 0.4189 | 0.9651 | 0.0000 | 0.0000 |
| pesq | spectral_gating | spectral_subtraction | 200.0000 | 40.0000 | 0.0666 | 0.0389 | 0.0945 | 0.7176 | 0.0001 | 0.0010 |
| pesq | spectral_gating | wiener | 200.0000 | 40.0000 | -0.1070 | -0.1576 | -0.0582 | -0.6634 | 0.0001 | 0.0010 |
| pesq | spectral_subtraction | wiener | 200.0000 | 40.0000 | -0.1736 | -0.2252 | -0.1253 | -1.0588 | 0.0000 | 0.0000 |
| stoi | noisy | spectral_gating | 200.0000 | 40.0000 | 0.0006 | -0.0020 | 0.0029 | 0.0710 | 0.2591 | 1.0000 |
| stoi | noisy | spectral_subtraction | 200.0000 | 40.0000 | -0.0007 | -0.0040 | 0.0025 | -0.0679 | 0.6273 | 1.0000 |
| stoi | noisy | wiener | 200.0000 | 40.0000 | 0.0000 | -0.0031 | 0.0030 | 0.0009 | 0.4517 | 1.0000 |
| stoi | spectral_gating | spectral_subtraction | 200.0000 | 40.0000 | -0.0013 | -0.0028 | 0.0001 | -0.2646 | 0.4762 | 1.0000 |
| stoi | spectral_gating | wiener | 200.0000 | 40.0000 | -0.0006 | -0.0017 | 0.0005 | -0.1621 | 0.7047 | 1.0000 |
| stoi | spectral_subtraction | wiener | 200.0000 | 40.0000 | 0.0007 | -0.0006 | 0.0021 | 0.1638 | 0.3974 | 1.0000 |
| reconstruction_snr_db | noisy | spectral_gating | 200.0000 | 40.0000 | 5.1694 | 4.7839 | 5.5781 | 3.9988 | 0.0000 | 0.0000 |
| reconstruction_snr_db | noisy | spectral_subtraction | 200.0000 | 40.0000 | 7.7196 | 6.9080 | 8.5066 | 3.0652 | 0.0000 | 0.0000 |
| reconstruction_snr_db | noisy | wiener | 200.0000 | 40.0000 | 6.2798 | 5.7647 | 6.7880 | 3.7393 | 0.0000 | 0.0000 |
| reconstruction_snr_db | spectral_gating | spectral_subtraction | 200.0000 | 40.0000 | 2.5502 | 2.1530 | 2.9597 | 1.8729 | 0.0000 | 0.0000 |
| reconstruction_snr_db | spectral_gating | wiener | 200.0000 | 40.0000 | 1.1104 | 0.9403 | 1.2860 | 1.9575 | 0.0000 | 0.0000 |
| reconstruction_snr_db | spectral_subtraction | wiener | 200.0000 | 40.0000 | -1.4397 | -1.7729 | -1.0835 | -1.2656 | 0.0000 | 0.0000 |
| snr_improvement_db | noisy | spectral_gating | 200.0000 | 40.0000 | 5.1694 | 4.7856 | 5.5712 | 3.9988 | 0.0000 | 0.0000 |
| snr_improvement_db | noisy | spectral_subtraction | 200.0000 | 40.0000 | 7.7196 | 6.9754 | 8.4775 | 3.0652 | 0.0000 | 0.0000 |
| snr_improvement_db | noisy | wiener | 200.0000 | 40.0000 | 6.2798 | 5.7433 | 6.7611 | 3.7393 | 0.0000 | 0.0000 |
| snr_improvement_db | spectral_gating | spectral_subtraction | 200.0000 | 40.0000 | 2.5502 | 2.1303 | 2.9579 | 1.8729 | 0.0000 | 0.0000 |
| snr_improvement_db | spectral_gating | wiener | 200.0000 | 40.0000 | 1.1104 | 0.9323 | 1.2857 | 1.9575 | 0.0000 | 0.0000 |
| snr_improvement_db | spectral_subtraction | wiener | 200.0000 | 40.0000 | -1.4397 | -1.7765 | -1.0873 | -1.2656 | 0.0000 | 0.0000 |

## Figures and waveform/spectrogram examples

![mean_pesq.png](figures/mean_pesq.png)
![mean_stoi.png](figures/mean_stoi.png)
![mean_reconstruction_snr_db.png](figures/mean_reconstruction_snr_db.png)
![mean_snr_improvement_db.png](figures/mean_snr_improvement_db.png)
![mean_processing_ms.png](figures/mean_processing_ms.png)
![distribution_pesq.png](figures/distribution_pesq.png)
![versus_input_snr_pesq.png](figures/versus_input_snr_pesq.png)
![by_noise_pesq.png](figures/by_noise_pesq.png)
![distribution_stoi.png](figures/distribution_stoi.png)
![versus_input_snr_stoi.png](figures/versus_input_snr_stoi.png)
![by_noise_stoi.png](figures/by_noise_stoi.png)
![distribution_snr_improvement_db.png](figures/distribution_snr_improvement_db.png)
![versus_input_snr_snr_improvement_db.png](figures/versus_input_snr_snr_improvement_db.png)
![by_noise_snr_improvement_db.png](figures/by_noise_snr_improvement_db.png)
![pesq_stoi_tradeoff.png](figures/pesq_stoi_tradeoff.png)

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

**REAL-RECORDING EXPERIMENT:** Manifest labels state audio provenance; objective metrics alone are not a listening study.

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
