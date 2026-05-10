from __future__ import annotations

import numpy as np


def confidence_from_uncertainty(uncertainty: np.ndarray) -> np.ndarray:
    return 1.0 / (1.0 + uncertainty)

