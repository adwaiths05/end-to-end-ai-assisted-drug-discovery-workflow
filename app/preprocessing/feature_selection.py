from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


def apply_variance_threshold(matrix: pd.DataFrame, preprocessor: Any) -> pd.DataFrame:
    values = preprocessor.transform(matrix.values) if hasattr(preprocessor, "transform") else matrix.values
    return pd.DataFrame(values, index=matrix.index)


def drop_correlated_features(matrix: pd.DataFrame, columns_to_drop: Any) -> pd.DataFrame:
    if columns_to_drop is None:
        return matrix
    if isinstance(columns_to_drop, (list, tuple, set)):
        drop_values = list(columns_to_drop)
        if drop_values and all(isinstance(item, (int, np.integer)) for item in drop_values):
            drop_names = [matrix.columns[idx] for idx in drop_values if 0 <= idx < len(matrix.columns)]
            return matrix.drop(columns=drop_names, errors="ignore")
        return matrix.drop(columns=drop_values, errors="ignore")
    if isinstance(columns_to_drop, np.ndarray):
        if columns_to_drop.dtype.kind in {"i", "u"}:
            drop_names = [matrix.columns[idx] for idx in columns_to_drop.tolist() if 0 <= int(idx) < len(matrix.columns)]
            return matrix.drop(columns=drop_names, errors="ignore")
        drop_names = columns_to_drop.tolist()
        return matrix.drop(columns=drop_names, errors="ignore")
    return matrix.drop(columns=columns_to_drop, errors="ignore")

