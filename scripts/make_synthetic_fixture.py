"""Generate synthetic proxy waveforms for software tests."""
import argparse
import json
from pathlib import Path
import numpy as np
from speech_benchmark.audio.loader import save_audio


def main():
    parser = argparse.ArgumentParser(description="Synthetic test-only benchmark dataset")
    parser.add_argument("--output", default="results/synthetic_validation/fixtures")
    args = parser.parse_args()
    root = Path(args.output)
    root.mkdir(parents=True, exist_ok=True)
    sr = 16000
    t = np.arange(2*sr) / sr
    rows = []
    for index in range(3):
        rng = np.random.default_rng(20240101 + index)
        fundamental = 110 + 20*index
        clean = (0.15 + 0.5*np.sin(2*np.pi*(1+index*.1)*t)**2) * (
            .30*np.sin(2*np.pi*fundamental*t) +
            .12*np.sin(2*np.pi*2*fundamental*t) +
            .08*np.sin(2*np.pi*3*fundamental*t))
        noise = .12*rng.standard_normal(len(t))
        if index == 1:
            noise += .09*np.sin(2*np.pi*150*t)
        save_audio(root / f"clean_{index}.wav", clean, sr)
        save_audio(root / f"noise_{index}.wav", noise, sr)
        rows.append({"id": f"synthetic_proxy_{index}",
                     "clean": f"clean_{index}.wav", "noise": f"noise_{index}.wav",
                     "noise_category": "synthetic_white_noise" if index != 1 else "synthetic_tonal_noise",
                     "clean_license": "original synthetic test fixture (MIT project)",
                     "noise_license": "original synthetic test fixture (MIT project)",
                     "clean_source": "scripts/make_synthetic_fixture.py — not a speech recording",
                     "noise_source": "scripts/make_synthetic_fixture.py — not an environmental recording"})
    (root / "manifest.json").write_text(json.dumps({"kind": "synthetic_test_only",
                                         "recordings": rows}, indent=2))
    print(f"Generated {len(rows)} synthetic software-test pairs: {root}")


if __name__ == "__main__":
    main()
