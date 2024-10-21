# Implemented spectral methods

The three methods implement `Denoiser.enhance(y, EnhancementContext)` and have a
fixed zero-lag waveform-length contract. All use the exact same STFT parameters and
`P_v(k) = mean_m |V(k,m)|²` from independent noise in oracle mode, or
`quantile_{0.20,m} |X(k,m)|²` for blind profile estimation.

## 1. Spectral subtraction (`algorithms/spectral_subtraction.py`)

`|S_hat(k,m)| = max(|X(k,m)|−beta sqrt(P_v(k)), floor × |X(k,m)|)`.

The complex STFT output retains the noisy input phase. `beta=1.15` and floor
`0.07` default. Noise underestimation leaves isolated spectral peaks and
**musical noise**; over-subtraction can remove harmonics, formants or weak unvoiced
speech. The spectral floor improves stability but leaves some audible background noise.

## 2. Spectral gating (`algorithms/spectral_gating.py`)

Compute `ratio=|X|/(threshold sqrt(P_v))`. A logistic soft mask is centered at ratio
1, then Gaussian-smoothed along frequency and time. Apply
`gain=clip(1−reduction×(1−mask), minimum_gain,1)`.

`threshold=1.5`, `reduction=0.92`, `minimum_gain=0.07`, frequency/time smoothing
standard deviations 1.5/1 bins. Strength: smooth easy-to-interpret spectral gate;
weakness: hard-to-estimate noise PSD; threshold can eliminate weak fricatives and
aggressive smoothing can blur short transients. In blind mode the 20th percentile is
not a true noise-only segment, especially for continuous speech.

## 3. Wiener filtering (`algorithms/wiener_filter.py`)

For additive, approximately uncorrelated clean speech and noise with PSDs `P_s` and
`P_v`, the scalar complex STFT linear MMSE estimator has Wiener gain
`G=P_s/(P_s+P_v)`. The implementation smooths the instantaneous mixture power using
`gaussian_filter`, estimates `P_s_hat=max(P_y_smoothed−P_v,0)`, then clamps gain to
`[min_gain,1]`. The default is minimum gain 0.06 and Gaussian stddev 1.5 frequency,
2.0 time bins. This is an **estimated linear MMSE spectral gain**, not an exact
Bayesian MMSE-STSA algorithm. PSD nonstationarity and missing harmonics can degrade
speech. Silence and zeros are stabilized by `1e−15` denominators.

## Optional neural algorithms

A legitimate model requires documented source, weights hash, training provenance,
license, sample rate and runtime. None is bundled or silently substituted. Registry
requests for `neural` fail explicitly, and the classical benchmark remains operational.

A neural enhancer would learn nonlinear speech priors from data and might handle
complex nonstationary noise better, but introduces training-distribution sensitivity,
large inference cost, possible language/speaker bias, and checkpoint licensing requirements.
It is not appropriate to label these hand-crafted spectral methods as AI models.
