from __future__ import annotations

import pandas as pd


def rank_candidates(frame: pd.DataFrame) -> pd.DataFrame:
    ordered = frame.copy()
    ordered["rank"] = ordered["predicted_pic50"].rank(ascending=False, method="dense").astype("Int64")
    return ordered.sort_values(["predicted_pic50", "confidence", "uncertainty"], ascending=[False, False, True]).reset_index(drop=True)

