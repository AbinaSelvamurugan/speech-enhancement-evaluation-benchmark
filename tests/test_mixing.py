import numpy as np
import pytest
from speech_benchmark.audio.mixing import mix_at_snr, select_noise
from speech_benchmark.utils.reproducibility import rng_for


@pytest.mark.parametrize("snr", [-5,0,5,10,15])
def test_snr_calibrated(synthetic_signal, snr):
    clean, noise, _ = synthetic_signal
    s, x, n, measured = mix_at_snr(clean, noise, snr)
    assert abs(measured - snr) < 1e-8
    np.testing.assert_allclose(x, s + n)
    assert np.max(abs(x)) <= .950001


def test_noise_offset_repeatable():
    arr = np.arange(137, dtype=float)
    a = select_noise(arr, 400, rng_for(100, "a"))
    b = select_noise(arr, 400, rng_for(100, "a"))
    np.testing.assert_array_equal(a, b)
    assert len(a) == 400


@pytest.mark.parametrize("silent_clean,silent_noise", [(True,False),(False,True)])
def test_silence_rejected(silent_clean, silent_noise):
    with pytest.raises(ValueError, match="non-negligible"):
        mix_at_snr(np.zeros(1000) if silent_clean else np.ones(1000),
                   np.zeros(1000) if silent_noise else np.ones(1000), 0)


def test_invalid_length():
    with pytest.raises(ValueError):
        mix_at_snr(np.ones(3), np.ones(4), 0)
