from __future__ import annotations

from app.inference.screening_service import ScreeningService


def predict_batch(smiles_list: list[str]) -> list[dict]:
    service = ScreeningService()
    return service.screen_smiles(smiles_list)

