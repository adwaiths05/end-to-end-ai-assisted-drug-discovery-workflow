from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class PredictionBundle:
    smiles: str
    canonical_smiles: str | None = None
    predicted_pic50: float | None = None
    confidence: float | None = None
    uncertainty: float | None = None
    agreement: float | None = None
    docking_affinity: float | None = None
    consensus_score: float | None = None
    valid: bool = True
    model_predictions: dict[str, float] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

