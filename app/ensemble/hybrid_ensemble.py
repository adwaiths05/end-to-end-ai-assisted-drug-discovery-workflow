from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from app.ensemble.meta_learner import predict_with_meta_learner
from app.ensemble.uncertainty import prediction_agreement, prediction_uncertainty


@dataclass
class EnsembleOutput:
    final_predictions: np.ndarray
    uncertainty: np.ndarray
    agreement: np.ndarray
    active_mode: str


def resolve_ensemble_mode(artifacts) -> str:
    if artifacts.ridge_hybrid is not None and artifacts.scaler_meta_hybrid is not None and artifacts.xgb_model is not None:
        return "hybrid"
    if artifacts.ridge_gnn is not None and artifacts.scaler_meta_gnn is not None and artifacts.mpnn_model is not None and artifacts.gin_model is not None:
        return "gnn"
    if artifacts.ridge_classical is not None and artifacts.scaler_meta_classical is not None and artifacts.rf_model is not None and artifacts.xgb_model is not None:
        return "classical"
    return "fallback"


def combine_predictions(artifacts, prediction_map: dict[str, np.ndarray]) -> EnsembleOutput:
    mode = resolve_ensemble_mode(artifacts)
    if mode == "hybrid":
        base_order = [prediction_map["rf"], prediction_map["xgb"], prediction_map["mpnn"], prediction_map["gin"]]
        matrix = np.column_stack(base_order)
        final = predict_with_meta_learner(matrix, artifacts.scaler_meta_hybrid, artifacts.ridge_hybrid)
        return EnsembleOutput(final, prediction_uncertainty(base_order), prediction_agreement(base_order), mode)
    if mode == "gnn":
        base_order = [prediction_map["mpnn"], prediction_map["gin"]]
        matrix = np.column_stack(base_order)
        final = predict_with_meta_learner(matrix, artifacts.scaler_meta_gnn, artifacts.ridge_gnn)
        return EnsembleOutput(final, prediction_uncertainty(base_order), prediction_agreement(base_order), mode)
    if mode == "classical":
        base_order = [prediction_map["rf"], prediction_map["xgb"]]
        matrix = np.column_stack(base_order)
        final = predict_with_meta_learner(matrix, artifacts.scaler_meta_classical, artifacts.ridge_classical)
        return EnsembleOutput(final, prediction_uncertainty(base_order), prediction_agreement(base_order), mode)
    base_order = [values for values in prediction_map.values() if values.size]
    if not base_order:
        return EnsembleOutput(np.array([], dtype=float), np.array([], dtype=float), np.array([], dtype=float), mode)
    final = np.nanmean(np.column_stack(base_order), axis=1)
    return EnsembleOutput(final, prediction_uncertainty(base_order), prediction_agreement(base_order), mode)

