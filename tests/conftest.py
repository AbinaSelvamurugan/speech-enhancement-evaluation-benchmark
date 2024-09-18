"""Algorithm plumbing fixtures built on synthetic signals."""
import json
import numpy as np
import pytest
import soundfile as sf


@pytest.fixture
def synthetic_signal():
    fs = 16000
    t = np.arange(32000) / fs
    # Harmonic voiced proxy, amplitude envelope, intentionally NOT human speech.
    envelope = 0.08 + 0.65 * np.sin(2 * np.pi * 1.3 * t)**2
    signal = envelope * (0.3*np.sin(2*np.pi*115*t) +
                         0.17*np.sin(2*np.pi*235*t) +
                         0.10*np.sin(2*np.pi*420*t))
    rng = np.random.default_rng(17)
    noise = rng.standard_normal(len(signal)) * .18
    return signal.astype(np.float64), noise.astype(np.float64), fs


@pytest.fixture
def synthetic_manifest(tmp_path, synthetic_signal):
    clean, noise, fs = synthetic_signal
    items = []
    for i in range(3):
        c = np.roll(clean, 100 * i)
        n = np.roll(noise, 123 * i) * (1 + 0.08*i)
        clean_path, noise_path = tmp_path / f"c{i}.wav", tmp_path / f"n{i}.wav"
        sf.write(clean_path, c, fs, subtype="FLOAT")
        sf.write(noise_path, n, fs, subtype="FLOAT")
        items.append({"id": f"synthetic_{i}", "clean": clean_path.name,
                      "noise": noise_path.name,
                      "noise_category": "synthetic_only_a" if i % 2 == 0 else "synthetic_only_b",
                      "clean_source": "Deterministic programmatic test generator, not real speech",
                      "noise_source": "Seeded Gaussian fixture, not environmental noise",
                      "clean_license": "generated for software tests",
                      "noise_license": "generated for software tests"})
    path = tmp_path / "manifest.json"
    path.write_text(json.dumps({"kind":"synthetic_test_only", "recordings":items}))
    return path
