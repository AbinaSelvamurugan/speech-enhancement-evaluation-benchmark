import numpy as np
import pytest
from speech_benchmark.audio.loader import load_audio, save_audio
from speech_benchmark.audio.resampling import resample
from speech_benchmark.audio.validation import mono_float, pair
from speech_benchmark.audio.alignment import align_known_zero_delay


def test_mono_stereo():
    signal = np.array([[1., 0.], [0., 1.]])
    np.testing.assert_allclose(mono_float(signal), [.5, .5])
    assert mono_float(np.ones((8, 1))).shape == (8,)


@pytest.mark.parametrize("bad", [np.array([]), np.ones((2,3)), np.array([float("nan")]),
                                   np.array([[1., float("inf")]])])
def test_invalid(bad):
    with pytest.raises(ValueError):
        mono_float(bad)


def test_soundfile_roundtrip(tmp_path):
    a = np.array([.22, -.36, .08, .15])
    path = tmp_path / "hello.wav"
    save_audio(path, a, 16000)
    b, sr = load_audio(path)
    assert sr == 16000
    np.testing.assert_allclose(a, b, atol=1e-7)


def test_missing_and_corrupt(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_audio(tmp_path / "missing.wav")
    p = tmp_path / "broken.wav"
    p.write_text("NOT A WAVE FILE")
    with pytest.raises(ValueError):
        load_audio(p)


@pytest.mark.parametrize("old,new", [(8000,16000),(16000,8000),(48000,16000),(16000,16000)])
def test_resampling(old, new):
    y = np.sin(2*np.pi*200*np.arange(old)/old)
    x = resample(y, old, new)
    assert len(x) == new
    assert np.all(np.isfinite(x))


def test_pair_alignment_rejects_time_shift():
    with pytest.raises(ValueError):
        align_known_zero_delay(np.ones(40), np.ones(39))
    with pytest.raises(ValueError):
        pair(np.ones(2), np.ones(3))


def test_stereo_file_downmix(tmp_path):
    import soundfile as sf
    wav = tmp_path / "stereo.wav"
    y = np.column_stack((np.ones(256) * .3, np.ones(256) * .1))
    sf.write(wav, y, 16000, subtype="FLOAT")
    got, _ = load_audio(wav)
    np.testing.assert_allclose(got, .2, atol=1e-7)
