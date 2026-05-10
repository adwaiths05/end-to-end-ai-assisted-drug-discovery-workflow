from __future__ import annotations

from app.inference.screening_service import ScreeningService


def predict_single(smiles: str) -> dict:
    service = ScreeningService()
    return service.screen_smiles([smiles])[0]

