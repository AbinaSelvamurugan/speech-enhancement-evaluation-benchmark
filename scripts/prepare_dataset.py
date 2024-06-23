"""Compatibility wrapper. Flags are identical to `speech-benchmark prepare`."""
import sys
from speech_benchmark.cli import main
if __name__ == "__main__":
    main(["prepare", *sys.argv[1:]])
