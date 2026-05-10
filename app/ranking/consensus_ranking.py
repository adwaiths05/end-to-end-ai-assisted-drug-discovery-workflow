from __future__ import annotations

import pandas as pd


def consensus_rank(frame: pd.DataFrame) -> pd.DataFrame:
    ranked = frame.copy()
    if "docking_affinity" in ranked.columns:
        ranked["rank_ml"] = ranked["predicted_pic50"].rank(ascending=False, method="dense")
        ranked["rank_docking"] = ranked["docking_affinity"].rank(ascending=True, method="dense")
        ranked["consensus_score"] = 1.0 / (ranked["rank_ml"] + ranked["rank_docking"])
        ranked = ranked.sort_values(["consensus_score", "predicted_pic50"], ascending=[False, False])
    return ranked.reset_index(drop=True)

