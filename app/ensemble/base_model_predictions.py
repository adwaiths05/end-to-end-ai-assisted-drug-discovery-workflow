from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd
import torch
from torch_geometric.loader import DataLoader


def predict_classical_model(model: Any, features: pd.DataFrame) -> np.ndarray:
    if model is None:
        return np.array([], dtype=float)
    values = features.values
    expected_features = getattr(model, "n_features_in_", None)
    if expected_features is not None and values.shape[1] < expected_features:
        padded = np.zeros((values.shape[0], expected_features), dtype=values.dtype)
        padded[:, : values.shape[1]] = values
        values = padded
    elif expected_features is not None and values.shape[1] > expected_features:
        values = values[:, :expected_features]
    if hasattr(model, "predict"):
        return np.asarray(model.predict(values), dtype=float)
    return np.asarray(model(values), dtype=float)


def predict_graph_model(model: torch.nn.Module | Any, graphs, batch_size: int = 32) -> np.ndarray:
    if model is None:
        return np.array([], dtype=float)
    loader = DataLoader(graphs, batch_size=batch_size, shuffle=False)
    model.eval()
    predictions: list[float] = []
    with torch.no_grad():
        for batch in loader:
            try:
                device = next(model.parameters()).device if hasattr(model, "parameters") else "cpu"
                batch = batch.to(device)
                output = model(batch)
                predictions.extend(output.detach().cpu().view(-1).tolist())
            except Exception as exc:
                model_name = type(model).__name__ if model is not None else "<None>"
                raise RuntimeError(
                    f"Graph model prediction failed for {model_name}: {type(exc).__name__}: {exc}"
                ) from exc
    return np.asarray(predictions, dtype=float)

