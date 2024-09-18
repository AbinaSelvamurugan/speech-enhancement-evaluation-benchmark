import importlib.util
import numpy as np
import pytest
from speech_benchmark.metrics.snr_metric import reconstruction_snr, snr_improvement
from speech_benchmark.metrics.pesq_metric import compute_pesq
from speech_benchmark.metrics.stoi_metric import compute_stoi
from speech_benchmark.audio.mixing import mix_at_snr


def test_reference_snr_and_improvement():
    clean = np.ones(16000) * .25
    noisy = clean + np.ones_like(clean)*.025
    enhanced = clean + np.ones_like(clean)*.0125
    assert reconstruction_snr(clean, noisy) == pytest.approx(20, abs=1e-9)
    assert reconstruction_snr(clean, enhanced) == pytest.approx(26.020599913, abs=1e-7)
    assert snr_improvement(clean, noisy, enhanced) == pytest.approx(6.020599913, abs=1e-7)


def test_reconstruction_snr_rejects_silence():
    with pytest.raises(ValueError):
        reconstruction_snr(np.zeros(100), np.zeros(100))


def test_synthetic_input_reconstruction_matches(synthetic_signal):
    s, v, fs = synthetic_signal
    clean, noisy, _, measured = mix_at_snr(s, v, -5)
    assert reconstruction_snr(clean, noisy) == pytest.approx(measured, abs=1e-8)


def test_pesq_invalid_mode_and_length():
    with pytest.raises(ValueError):
        compute_pesq(np.ones(16000), np.ones(16000), 8000, "wb")
    with pytest.raises(ValueError):
        compute_pesq(np.ones(16000), np.ones(15999), 16000, "wb")


def test_pesq_binding_missing_is_reported(synthetic_signal):
    if importlib.util.find_spec("pesq") is not None:
        pytest.skip("Dependency installed; run native PESQ smoke test")
    signal, _, fs = synthetic_signal
    with pytest.raises(RuntimeError, match="dependency unavailable"):
        compute_pesq(signal, signal, fs, "wb")


@pytest.mark.pesq
def test_pesq_library_when_installed(synthetic_signal):
    pytest.importorskip("pesq")
    clean, noise, fs = synthetic_signal
    s, mixture, _, _ = mix_at_snr(clean, noise, 5)
    # This is a **library smoke test** on synthetic audio, not a speech quality claim.
    assert np.isfinite(compute_pesq(s, mixture, fs, "wb"))


def test_stoi_real_library_on_fixture(synthetic_signal):
    signal, noise, fs = synthetic_signal
    s, mixture, _, _ = mix_at_snr(signal, noise, 5)
    result = compute_stoi(s, mixture, fs)
    assert np.isfinite(result) and -1 <= result <= 1


def test_stoi_rejects_short_silent_and_invalid_fs(synthetic_signal):
    signal, _, fs = synthetic_signal
    with pytest.raises(ValueError):
        compute_stoi(signal[:200], signal[:200], fs)
    with pytest.raises(ValueError):
        compute_stoi(np.zeros(fs), np.zeros(fs), fs)
    with pytest.raises(ValueError):
        compute_stoi(signal, signal, 4000)


def test_stoi_eight_khz_and_resampling(synthetic_signal):
    from speech_benchmark.audio.resampling import resample
    clean, noise, sr = synthetic_signal
    s = resample(clean, sr, 8000)
    v = resample(noise, sr, 8000)
    ref, mix, _, _ = mix_at_snr(s, v, 0)
    assert np.isfinite(compute_stoi(ref, mix, 8000))


def test_pesq_nonfinite_reference():
    with pytest.raises(ValueError):
        compute_pesq(np.full(16000, np.nan), np.ones(16000), 16000, "wb")
