# Exact objective metrics and limitations

## PESQ

The `pesq==0.0.4` Python wrapper calls the published PESQ C implementation.
`pesq(fs, ref, degraded, mode, on_error=PesqError.RAISE_EXCEPTION)` is used directly;
there is **no fallback score**. The binding accepts narrowband at 8 or 16 kHz and
wideband at 16 kHz; for this benchmark, use narrowband **only at 8 kHz** and
wideband **only at 16 kHz** to prevent incomparable mixes. Ref and degraded must be
finite, 1D, same length, same sample rate and corresponding zero-lag utterances.
Metric exceptions return missing values with an `errors.pesq` explanation.
PESQ approximate listening quality is not human MOS ground truth.

**Licensing:** PESQ sources/IP carry their own usage restrictions. Installing an open
Python wrapper does **not** grant permission for unrestricted commercial PESQ use. Review
`pesq` package/ITU terms for your use case and arrange licenses when necessary.
**Standard status:** ITU withdrew its P.862/P.862.1/P.862.2/P.862.3 recommendations
on 5 January 2024, directing users to newer P.863-series standards.
References: https://pypi.org/project/pesq/ and https://www.itu.int/rec/T-REC-P.862 .

## STOI

`pystoi==0.4.1`, `pystoi.stoi(ref, degraded, fs_sig, extended=False)` is called
directly. Ordinary STOI is the default; `extended=True` selects ESTOI and must be
reported as a separate metric mode, not mixed with STOI aggregates. The algorithm
internally resamples to its prescribed analysis rate where necessary; the benchmark
pre-resamples all audio to the **same** 8/16 kHz evaluation rate with SciPy polyphase
and avoids post hoc shifting. STOI estimates intelligibility and cannot guarantee
human understanding, especially in far-field, multilingual or heavily distorted audio.

## Synthetic input SNR versus reconstruction SNR

Known mixture `x=s+v_scaled`: `input_snr=10log10(sum(s²)/sum(v_scaled²))`.

With any enhanced waveform `s_hat`, define
`reconstruction_snr=10log10(mean(s²)/max(mean((s−s_hat)²),1e−12))`.

**This is not pure residual-noise SNR**; it penalizes speech attenuation, gain mismatch
and distortions. Its baseline counterpart `reconstruction_snr(s,x)` equals the measured
synthetic mixture input SNR. `delta_reconstruction_snr = recon_snr(s,s_hat) −
recon_snr(s,x)`; comparing to the same baseline supports valid paired differences.
For perfect reconstruction, the finite floor limits the score; this is an explicitly
*floor-capped* reconstruction SNR, not mathematically +infinity.

**SI-SDR** optimizes a single gain factor between estimate and clean (is scale-invariant);
reconstruction SNR penalizes gain errors, so they answer different questions. SNR can
rise when intelligibility or PESQ falls if speech energy is removed. Never rank speech
quality solely by SNR.

The metrics may fail independently; each row retains `errors` as a JSON string and
`status=metric_partial`; missing scores never become zeros in statistics or charts.
