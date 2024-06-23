"""Compatibility wrapper. Flags are identical to `speech-benchmark report`."""
import sys
from speech_benchmark.cli import main
if __name__ == "__main__":
    main(["report", *sys.argv[1:]])
