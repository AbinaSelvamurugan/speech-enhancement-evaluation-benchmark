# Audio data and manifest

Benchmark audio is not bundled. Download it under the terms of each source. PESQ carries
its own evaluation rights and licensing.

For a real benchmark, start with:

- LibriSpeech *test-clean* (CC BY 4.0): https://www.openslr.org/12/
  Attribution: Panayotov et al., *LibriSpeech*, ICASSP 2015. Use independent speakers and utterances.
- DEMAND environmental noise (CC BY-SA 3.0):
  https://zenodo.org/records/1227121 ; Thiemann et al., 2013. Note the redistribution and share-alike terms.
- MS-SNSD recipe and provenance notes:
  https://github.com/microsoft/MS-SNSD ; Reddy et al., Interspeech 2019.

Each noise category should match the content of the source recordings. Do not train
algorithms on evaluation clean utterances; the default classical algorithms are not trained.
The `oracle` PSD condition uses known independent synthetic noise, while the `blind`
condition estimates the PSD from the mixture alone.

Create `data/manifest.json` yourself after obtaining audio:

```json
{
  "kind": "real_recordings",
  "recordings": [
    {
      "id": "speaker123_utterance004_fan01",
      "clean": "speech/speaker123/004.flac",
      "noise": "noise/fan01.wav",
      "noise_category": "fan",
      "clean_source": "https://www.openslr.org/12/",
      "noise_source": "https://zenodo.org/records/1227121",
      "clean_license": "CC BY 4.0",
      "noise_license": "CC BY-SA 3.0"
    }
  ]
}
```

Paths are relative to `data/manifest.json`. The program checks that files exist and hashes
the originals; provenance and content identification are the researcher's responsibility.
A unique `id` identifies a speech/noise *pair*, while bootstrap clustering uses
`recording_id`. For strict speaker independence, make the ID a speaker identifier and use
one utterance per speaker per noise condition, or extend the grouping with an explicit
speaker field. Prefer multiple independent speakers and independent noise *recordings* over
many crops of one long file, and record source, train/test split and license accurately.

The synthetic validation fixtures under [`../examples/synthetic_validation/`](../examples/synthetic_validation/)
are generated test audio, not clean speech recordings.
