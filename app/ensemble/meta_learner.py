from __future__ import annotations

from typing import Any

import numpy as np


def predict_with_meta_learner(predictions: np.ndarray, scaler: Any, ridge_model: Any) -> np.ndarray:
    if predictions.size == 0:
        return np.array([], dtype=float)
    scaled = scaler.transform(predictions) if scaler is not None and hasattr(scaler, "transform") else predictions
    if ridge_model is None:
        return np.asarray(predictions.mean(axis=1), dtype=float)
    return np.asarray(ridge_model.predict(scaled), dtype=float)

