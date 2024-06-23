"""Compatibility wrapper. Flags are identical to `speech-benchmark run`."""
import sys
from speech_benchmark.cli import main
if __name__ == "__main__":
    main(["run", *sys.argv[1:]])
