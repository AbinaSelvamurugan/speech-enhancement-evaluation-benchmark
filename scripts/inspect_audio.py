"""Compatibility wrapper. Flags are identical to `speech-benchmark inspect`."""
import sys
from speech_benchmark.cli import main
if __name__ == "__main__":
    main(["inspect", *sys.argv[1:]])
