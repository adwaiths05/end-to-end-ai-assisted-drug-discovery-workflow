from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from app.analysis.molecule_inspector import inspect_molecule
from app.config import settings
from app.ensemble.base_model_predictions import predict_classical_model, predict_graph_model
from app.ensemble.hybrid_ensemble import combine_predictions
from app.graph.batch_graph_builder import build_graphs
from app.models.artifact_loader import LoadedArtifacts, load_artifacts
from app.preprocessing.pipeline import ClassicalFeaturePipeline
from app.ranking.candidate_ranking import rank_candidates
from app.ranking.confidence_scoring import confidence_from_uncertainty
from app.validation.molecule_standardization import standardize_molecule
from app.validation.smiles_validation import is_valid_smiles

LOGGER = logging.getLogger(__name__)


class ScreeningService:
    def __init__(self, artifacts: LoadedArtifacts | None = None) -> None:
        self.artifacts = artifacts or load_artifacts()
        self.pipeline = ClassicalFeaturePipeline(self.artifacts.preproc_vt, self.artifacts.preproc_scaler, self.artifacts.preproc_to_drop)

    def _prepare_inputs(self, smiles_list: list[str], compound_ids: list[str] | None = None) -> tuple[list[dict], list[str]]:
        records = []
        valid_smiles = []
        for i, smiles in enumerate(smiles_list):
            comp_id = compound_ids[i] if compound_ids and i < len(compound_ids) else f"ligand_{i}"
            if not is_valid_smiles(smiles):
                records.append({"smiles": smiles, "valid": False, "canonical_smiles": None, "compound_id": comp_id})
                continue
            standardized = standardize_molecule(smiles) or smiles
            valid_smiles.append(standardized)
            records.append({"smiles": smiles, "valid": True, "canonical_smiles": standardized, "compound_id": comp_id})
        return records, valid_smiles

    def screen_smiles(self, smiles_list: list[str], top_n: int | None = None, compound_ids: list[str] | None = None) -> list[dict]:
        records, valid_smiles = self._prepare_inputs(smiles_list, compound_ids)
        if not valid_smiles:
            return records

        feature_frame = self.pipeline.transform(valid_smiles)
        graphs, valid_graph_indices = build_graphs(valid_smiles)
        valid_feature_frame = feature_frame.iloc[valid_graph_indices].reset_index(drop=True) if len(valid_graph_indices) != len(valid_smiles) else feature_frame.reset_index(drop=True)

        predictions: dict[str, np.ndarray] = {}
        if self.artifacts.rf_model is not None:
            predictions["rf"] = predict_classical_model(self.artifacts.rf_model, valid_feature_frame)
        if self.artifacts.xgb_model is not None:
            predictions["xgb"] = predict_classical_model(self.artifacts.xgb_model, valid_feature_frame)
        if self.artifacts.mpnn_model is not None and graphs:
            predictions["mpnn"] = predict_graph_model(self.artifacts.mpnn_model, graphs)
        if self.artifacts.gin_model is not None and graphs:
            predictions["gin"] = predict_graph_model(self.artifacts.gin_model, graphs)

        if not predictions:
            for record in records:
                record.update({"status": "no_models_available"})
            return records

        ensemble = combine_predictions(self.artifacts, predictions)
        confidence = confidence_from_uncertainty(ensemble.uncertainty)
        
        max_length = len(valid_smiles)
        final_preds = ensemble.final_predictions
        unc = ensemble.uncertainty
        conf = confidence
        agr = ensemble.agreement
        
        if len(final_preds) != max_length:
            padded_preds = np.full(max_length, np.nan)
            padded_preds[:len(final_preds)] = final_preds
            final_preds = padded_preds
            
            padded_unc = np.full(max_length, np.nan)
            padded_unc[:len(unc)] = unc
            unc = padded_unc
            
            padded_conf = np.full(max_length, np.nan)
            padded_conf[:len(conf)] = conf
            conf = padded_conf
            
            padded_agr = np.full(max_length, np.nan)
            padded_agr[:len(agr)] = agr
            agr = padded_agr
            
            for key, value in list(predictions.items()):
                padded = np.full(max_length, np.nan)
                padded[:len(value)] = value
                predictions[key] = padded

        result_frame = pd.DataFrame(
            {
                "smiles": valid_smiles,
                "compound_id": [r["compound_id"] for r in records if r["valid"]],
                "predicted_pic50": final_preds,
                "uncertainty": unc,
                "confidence": conf,
                "agreement": agr,
                "rf_pred": predictions.get("rf"),
                "xgb_pred": predictions.get("xgb"),
                "mpnn_pred": predictions.get("mpnn"),
                "gin_pred": predictions.get("gin"),
            }
        )
        result_frame = rank_candidates(result_frame)

        valid_records = []
        for row in result_frame.to_dict(orient="records"):
            row["valid"] = True
            row["status"] = "success"
            # Use inspect_molecule once to get all properties
            mol_data = inspect_molecule(row["smiles"], {"ensemble_mode": ensemble.active_mode})
            # Map molecular properties to the "metadata" format expected by the frontend
            row["metadata"] = {
                "mw": mol_data.get("molecular_weight", 0),
                "logp": mol_data.get("logp", 0),
                "hbd": mol_data.get("hbd", 0),
                "hba": mol_data.get("hba", 0),
                "rotatable_bonds": mol_data.get("rotatable_bonds", 0),
                "tpsa": mol_data.get("tpsa", 0),
                "ensemble_mode": ensemble.active_mode
            }
            # Keep original mol_properties for DB storage
            row["mol_properties"] = mol_data
            model_predictions = {}
            for key in ("rf", "xgb", "mpnn", "gin"):
                column = f"{key}_pred"
                if column in row and row[column] is not None:
                    try:
                        model_predictions[key] = float(row[column])
                    except Exception:
                        continue
            row["model_predictions"] = model_predictions
            valid_records.append(row)

        invalid_records = []
        for record in records:
            if not record.get("valid"):
                record.update({"status": "invalid_smiles", "predicted_pic50": None, "confidence": None, "uncertainty": None, "agreement": None})
                invalid_records.append(record)

        if top_n is not None:
            # Top-N mode should return exactly N ranked hits, not extra invalid rows.
            return valid_records[:top_n]

        return valid_records + invalid_records

