from __future__ import annotations

from typing import Any

import pandas as pd


def scale_features(matrix: pd.DataFrame, scaler: Any) -> pd.DataFrame:
    values = scaler.transform(matrix.values) if hasattr(scaler, "transform") else matrix.values
    return pd.DataFrame(values, index=matrix.index)

