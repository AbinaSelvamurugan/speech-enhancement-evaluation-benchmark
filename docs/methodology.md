# DSP methodology for an ECE engineer

## Signal chain and timing

```text
Licensed clean speech s[n] ──┐
                             ├─ SNR-controlled sum ─ x[n] ─┬─ Noisy reference
Licensed environmental v[n]┘                              ├─ Subtraction ─ ŝ₁[n]
        │ (oracle *only*)                                   ├─ Gating ─ ŝ₂[n]
        └────────── estimated noise PSD ────────────────────└─ Wiener ─ ŝ₃[n]
                          │                                  │
                          └── profile mode recorded ─────────┤
                                 aligned clean reference ────┘
                                    │
                    PESQ / STOI / reconstruction SNR / runtime
                                    │
                          per-case CSV → cluster stats → charts/report
```

All clip processing is on a deterministic mono, float64 8 or 16 kHz grid.
SoundFile reads with `always_2d=True`; stereo downmix is the arithmetic mean of channels
(could lead to phase cancellation; note in an external dataset's metadata). The
`scipy.signal.resample_poly` rational FIR anti-aliasing resamples once, before any mixtures,
and is not timed. Resampling may affect boundary samples. Only the exact first
`segment_seconds` of a clean recording is scored; reject speech with insufficient power.
Noise wraps if shorter, with random offset seeded from stable hash of dataset identifier;
wrapping can create periodic noise, so prefer longer recordings than segment length.

## Example SNR calculation

For 4-second s and v with average powers `Ps=.0100`, `Pv=.0400` and target 5 dB:

`alpha = sqrt(0.0100/(0.0400 × 10^(5/10))) = 0.2812`.

Mix `x=s+alpha*v`. The added noise has power about `0.003162`, giving 5 dB input
SNR. If the combined peak exceeds 0.95, all three reference, mixture and actual noise
are scaled equally to keep 32-bit WAVs within practical playback range. This common
gain does not change actual SNR; it also avoids confusing clipping with denoising.
The actual SNR is recomputed from s and added noise; numerically it equals the
noisy reconstruction SNR because `x−s` is the added noise.

## STFT and overlap-add

For window `w[n]`, length `N`, hop `H`, Fourier bin `k` and frame `m`:

`X(m,k) = sum_{n=0}^{N−1} x[n+mH] w[n] exp(−j2πkn/N)`.

Windowing localizes time-frequency structure and reduces leakage. Reconstruct with
SciPy's inverse STFT using **the same Hann window, frame size, overlap, padding and
boundary convention**. Inverse STFT normalizes overlapping window contributions and
restores the exact original length; STFT/ISTFT identity holds numerically even when
sample length is not an integer number of hops. `nperseg=512`, `hop=128` gives 32 ms
frames and 8 ms hops at 16 kHz. Window choice affects temporal resolution, spectral
leakage and the musical-noise/phoneme preservation tradeoff.

## Fairness controls and leakage

- Every denoiser receives `.copy()` of **identical** input sample arrays.
- The same independent scaled noise reference is used by all denoisers in `oracle`
  mode; in `blind` mode none receives clean or known noise.
- Metrics see the same untouched aligned clean array, no per-method gain correction.
- STFT algorithms are zero-delay. Length mismatch triggers error; don't maximize
  metrics by retrospective time shifts. Methods with known fixed latency need an
  independently calibrated delay adapter before benchmarking.
- Oracle PSD measures average squared STFT magnitude of *only* the independent
  noise component, a privileged synthetic experiment. A blind profile uses 20th
  percentile of mixture power for each frequency bin and can confuse low-energy
  speech with background noise. Report both strategies as separate studies.
- Parameters must be fixed before opening held-out evaluation results; otherwise
  repeated tuning on the test set leaks evaluation information.
- The mixture SHA256s are derivable from clean/noise hashes, seed, and configuration.
- Saved output uses 32-bit floating WAV (no output hard limiting). Evaluated data
  are in-memory float64, not the exported 32-bit float, minimizing score dependence
  on serialization; exported audio is for listening/illustration.

## Cost and reproducibility

`processing_ms` clocks **only** `.enhance()`, after deterministic 1-second sine warmup
when enabled. No load, resampling, metric, report generation, audio save or Python
process start is included. `RTF=processing_seconds/clip_seconds` (lower is faster).
Repeated timing trials and machine isolation would be needed for tight latency estimates;
small time differences are descriptive, not statistically calibrated. `run_metadata.json`
contains config and manifest SHA256, original audio SHA256, original dataset licenses,
Python/NumPy/SciPy versions, and timing protocol.

## Real-world generalization

Source clean speech need not be perfectly noise-free; room reverberation and silence can
change PESQ/STOI. Avoid short utterances, unequal recording gains and speech-dependent
sampling bias. Report number of distinct speakers and independent noise environments;
multiple SNR versions of one utterance are **correlated**, not new observations.
With one utterance per independent recording ID, recording-cluster resampling is valid;
with multiple recordings per speaker, extend clustering by speaker identity for speaker-level
inference. A distinct fixed noise recording shared across many recordings may warrant
two-way speaker/noise clustering in a large study. Results should be treated as descriptive
without this independence.
