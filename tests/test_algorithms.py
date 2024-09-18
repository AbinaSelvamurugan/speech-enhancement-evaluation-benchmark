import numpy as np
import pytest
from speech_benchmark.algorithms.base import EnhancementContext
from speech_benchmark.algorithms.registry import create, REGISTRY
from speech_benchmark.algorithms.neural_denoiser import availability
from speech_benchmark.audio.mixing import mix_at_snr


@pytest.mark.parametrize("name", list(REGISTRY))
@pytest.mark.parametrize("profile", ["oracle", "blind"])
def test_method_integrity(synthetic_signal, name, profile):
    clean, noise, fs = synthetic_signal
    s, mixture, v, _ = mix_at_snr(clean, noise, 5)
    untouched = mixture.copy()
    method = create(name)
    output = method.enhance(mixture, EnhancementContext(fs,
                             noise_reference=v if profile == "oracle" else None,
                             noise_profile=profile))
    assert output.shape == mixture.shape
    assert output is not mixture
    assert np.all(np.isfinite(output))
    np.testing.assert_array_equal(mixture, untouched)
    if name == "noisy":
        np.testing.assert_array_equal(output, mixture)


def test_missing_noise_profile(synthetic_signal):
    s, v, fs = synthetic_signal
    with pytest.raises(ValueError, match="independent noise reference"):
        create("wiener").enhance(s, EnhancementContext(fs, None, "oracle"))


def test_unknown_and_missing_neural():
    with pytest.raises(RuntimeError, match="unavailable"):
        create("neural")
    with pytest.raises(ValueError):
        create("imagined_filter")
    assert availability()[0] is False


def test_zero_input_blind_finite():
    for name in list(REGISTRY):
        y = create(name).enhance(np.zeros(16001), EnhancementContext(16000, None, "blind"))
        assert np.all(np.isfinite(y)) and len(y) == 16001


def test_bad_parameters():
    with pytest.raises(ValueError):
        create("spectral_subtraction", {"spectral_subtraction": {"spectral_floor":-1}})
    with pytest.raises(ValueError):
        create("spectral_gating", {"spectral_gating": {"reduction_strength":2}})
    with pytest.raises(ValueError):
        create("wiener", {"wiener": {"min_gain":2}})
