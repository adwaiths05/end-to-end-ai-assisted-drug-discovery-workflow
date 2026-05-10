from __future__ import annotations

import numpy as np


def safe_mean(values: list[float]) -> float:
    if not values:
        return 0.0
    return float(np.mean(values))


def safe_std(values: list[float]) -> float:
    if len(values) < 2:
        return 0.0
    return float(np.std(values, ddof=0))

