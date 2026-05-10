from __future__ import annotations

import __main__
import logging
import pickle
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
import torch

from app.config import settings
from app.models.gnn_models import EdgeAwareMPNN, GINBlock, GINModel, GraphStructureLearning

LOGGER = logging.getLogger(__name__)


for cls in (EdgeAwareMPNN, GINModel, GINBlock, GraphStructureLearning):
    setattr(__main__, cls.__name__, cls)

# Backward compatibility aliases for checkpoints saved from notebooks/scripts
# where model classes used different names under __main__.
setattr(__main__, "MPNNModel", EdgeAwareMPNN)
setattr(__main__, "GINNet", GINModel)


@dataclass
class LoadedArtifacts:
    rf_model: Any | None = None
    xgb_model: Any | None = None
    mpnn_model: Any | None = None
    gin_model: Any | None = None
    ridge_classical: Any | None = None
    ridge_gnn: Any | None = None
    ridge_hybrid: Any | None = None
    scaler_meta_classical: Any | None = None
    scaler_meta_gnn: Any | None = None
    scaler_meta_hybrid: Any | None = None
    preproc_vt: Any | None = None
    preproc_scaler: Any | None = None
    preproc_to_drop: Any | None = None
    preproc_pca: Any | None = None
    active_models: tuple[str, ...] = field(default_factory=tuple)


def _load_pickle(path: Path) -> Any:
    with path.open("rb") as handle:
        return pickle.load(handle)


def _load_joblib_or_pickle(path: Path) -> Any:
    try:
        return joblib.load(path)
    except Exception:
        return _load_pickle(path)


def _load_torch_model(path: Path, model_cls: type[torch.nn.Module]) -> torch.nn.Module:
    try:
        payload = torch.load(path, map_location="cpu", weights_only=False)
    except TypeError:
        payload = torch.load(path, map_location="cpu")
    if isinstance(payload, torch.nn.Module):
        return payload
    model = model_cls()
    if isinstance(payload, dict):
        state_dict = payload.get("state_dict", payload)
        model.load_state_dict(state_dict, strict=False)
    return model


@lru_cache(maxsize=1)
def load_artifacts() -> LoadedArtifacts:
    artifact_dir = settings.artifact_dir
    artifacts = LoadedArtifacts()

    def optional(path_name: str, loader) -> Any | None:
        path = artifact_dir / path_name
        if not path.exists():
            LOGGER.warning("Missing artifact: %s", path)
            return None
        LOGGER.info("Loading artifact: %s", path)
        return loader(path)

    artifacts.rf_model = optional("rf_final.pkl", _load_joblib_or_pickle)
    artifacts.xgb_model = optional("xgb_final.pkl", _load_joblib_or_pickle)
    artifacts.mpnn_model = optional("mpnn_final_reg.pt", lambda p: _load_torch_model(p, EdgeAwareMPNN))
    artifacts.gin_model = optional("gin_final_reg.pt", lambda p: _load_torch_model(p, GINModel))
    artifacts.ridge_classical = optional("ridge_classical.pkl", _load_joblib_or_pickle)
    artifacts.ridge_gnn = optional("ridge_gnn.pkl", _load_joblib_or_pickle)
    artifacts.ridge_hybrid = optional("ridge_hybrid.pkl", _load_joblib_or_pickle)
    artifacts.scaler_meta_classical = optional("scaler_meta_classical.pkl", _load_joblib_or_pickle)
    artifacts.scaler_meta_gnn = optional("scaler_meta_gnn.pkl", _load_joblib_or_pickle)
    artifacts.scaler_meta_hybrid = optional("scaler_meta_hybrid.pkl", _load_joblib_or_pickle)
    artifacts.preproc_vt = optional("preproc_vt.pkl", _load_joblib_or_pickle)
    artifacts.preproc_scaler = optional("preproc_scaler.pkl", _load_joblib_or_pickle)
    artifacts.preproc_to_drop = optional("preproc_to_drop.pkl", _load_joblib_or_pickle)
    artifacts.preproc_pca = optional("preproc_pca.pkl", _load_joblib_or_pickle)

    active = []
    for name in ("rf", "xgb", "mpnn", "gin"):
        if getattr(artifacts, f"{name}_model") is not None:
            active.append(name)
    artifacts.active_models = tuple(active)
    return artifacts

