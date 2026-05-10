from __future__ import annotations

import numpy as np


def prediction_uncertainty(base_predictions: list[np.ndarray]) -> np.ndarray:
    if not base_predictions:
        return np.array([], dtype=float)
    stacked = np.vstack(base_predictions)
    return np.nanstd(stacked, axis=0)


def prediction_agreement(base_predictions: list[np.ndarray]) -> np.ndarray:
    if not base_predictions:
        return np.array([], dtype=float)
    stacked = np.vstack(base_predictions)
    return 1.0 / (1.0 + np.nanstd(stacked, axis=0))

