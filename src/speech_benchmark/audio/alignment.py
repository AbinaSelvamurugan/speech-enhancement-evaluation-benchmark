"""Zero-delay contract. Never optimize metric scores with correlation shifting."""
import numpy as np
from .validation import pair


def align_known_zero_delay(clean: np.ndarray, enhanced: np.ndarray):
    """Require exact same duration; denoisers preserve sample indices.

    There is no post hoc time-shift search, tail truncation, or ref-dependent alignment.
    Externally delayed algorithms must provide a calibrated, fixed delay adapter.
    """
    return pair(clean, enhanced)
