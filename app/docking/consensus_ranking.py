from __future__ import annotations

import logging
from dataclasses import dataclass

import pandas as pd

LOGGER = logging.getLogger(__name__)


@dataclass
class ConsensusRank:
    """Consensus ranking combining ML and docking scores."""

    rank: int
    ligand_id: str
    smiles: str
    predicted_pic50: float | None
    docking_affinity: float | None
    ml_rank: int | None
    docking_rank: int | None
    consensus_score: float

    def to_dict(self) -> dict:
        return {
            "rank": self.rank,
            "ligand_id": self.ligand_id,
            "smiles": self.smiles,
            "predicted_pic50": self.predicted_pic50,
            "docking_affinity": self.docking_affinity,
            "ml_rank": self.ml_rank,
            "docking_rank": self.docking_rank,
            "consensus_score": self.consensus_score,
        }


class ConsensusRanker:
    """Rank ligands by consensus of ML predictions and docking affinities."""

    @staticmethod
    def rank(
        docking_results: list[dict],
        ml_predictions: list[dict] | None = None,
        ml_weight: float = 0.5,
        dock_weight: float = 0.5,
    ) -> list[ConsensusRank]:
        """
        Combine ML and docking scores into consensus ranking.

        Args:
            docking_results: List of docking results with smiles, vina_affinity, etc.
            ml_predictions: List of ML predictions with predicted_pic50
            ml_weight: Weight for ML predictions (0-1)
            dock_weight: Weight for docking scores (0-1)

        Returns:
            List of ConsensusRank objects, sorted by consensus score.
        """
        if ml_weight + dock_weight != 1.0:
            ml_weight = ml_weight / (ml_weight + dock_weight)
            dock_weight = dock_weight / (ml_weight + dock_weight)

        # Build dataframe from docking results
        dock_df = pd.DataFrame(docking_results)

        # Match with ML predictions if provided
        if ml_predictions:
            ml_df = pd.DataFrame(ml_predictions)
            # Merge on smiles if available
            if "smiles" in dock_df.columns and "smiles" in ml_df.columns:
                combined = dock_df.merge(ml_df, on="smiles", how="left", suffixes=("_dock", "_ml"))
            else:
                # Match by index
                combined = dock_df.copy()
                for idx, row in ml_df.iterrows():
                    if idx < len(combined):
                        combined.loc[idx, "predicted_pic50"] = row.get("predicted_pic50")
        else:
            combined = dock_df.copy()

        # Calculate ranks
        # ML rank: lower pIC50 is better (higher rank value)
        if "predicted_pic50" in combined.columns:
            combined["ml_rank"] = combined["predicted_pic50"].rank(ascending=False, na_option="bottom")
        else:
            combined["ml_rank"] = float("nan")

        # Docking rank: lower affinity (more negative) is better (higher rank value)
        if "vina_affinity" in combined.columns:
            combined["dock_rank"] = combined["vina_affinity"].rank(ascending=True, na_option="bottom")
        else:
            combined["dock_rank"] = float("nan")

        # Calculate consensus score (normalized ranks weighted)
        max_rank = len(combined)
        combined["ml_score"] = (
            (max_rank - combined["ml_rank"]) / max_rank if "ml_rank" in combined.columns else 0
        )
        combined["dock_score"] = (
            (max_rank - combined["dock_rank"]) / max_rank if "dock_rank" in combined.columns else 0
        )

        # Fill NaNs with 0
        combined["ml_score"] = combined["ml_score"].fillna(0)
        combined["dock_score"] = combined["dock_score"].fillna(0)

        combined["consensus_score"] = (
            ml_weight * combined["ml_score"] + dock_weight * combined["dock_score"]
        )

        # Sort by consensus score (descending)
        combined = combined.sort_values("consensus_score", ascending=False).reset_index(drop=True)

        # Build results
        results = []
        for idx, row in combined.iterrows():
            result = ConsensusRank(
                rank=idx + 1,
                ligand_id=row.get("name", row.get("compound_id", f"lig_{idx:03d}")),
                smiles=row["smiles"],
                predicted_pic50=row.get("predicted_pic50"),
                docking_affinity=row.get("vina_affinity"),
                ml_rank=int(row["ml_rank"]) if pd.notna(row["ml_rank"]) else None,
                docking_rank=int(row["dock_rank"]) if pd.notna(row["dock_rank"]) else None,
                consensus_score=float(row["consensus_score"]),
            )
            results.append(result)

        LOGGER.info(f"Ranked {len(results)} ligands by consensus")
        return results
