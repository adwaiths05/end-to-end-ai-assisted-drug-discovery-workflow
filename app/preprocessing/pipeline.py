from __future__ import annotations

import pandas as pd

from app.preprocessing.descriptors import DESC_NAMES, calculate_descriptors
from app.preprocessing.feature_scaling import scale_features
from app.preprocessing.feature_selection import apply_variance_threshold, drop_correlated_features
from app.preprocessing.fingerprints import morgan_fingerprint


class ClassicalFeaturePipeline:
    def __init__(self, vt=None, scaler=None, to_drop=None) -> None:
        self.vt = vt
        self.scaler = scaler
        self.to_drop = to_drop

    def transform(self, smiles_list: list[str]) -> pd.DataFrame:
        descriptor_rows = [calculate_descriptors(smiles) for smiles in smiles_list]
        descriptor_frame = pd.DataFrame(descriptor_rows, columns=DESC_NAMES)
        if self.vt is not None:
            descriptor_frame = apply_variance_threshold(descriptor_frame, self.vt)
        descriptor_frame = drop_correlated_features(descriptor_frame, self.to_drop)
        if self.scaler is not None:
            descriptor_frame = scale_features(descriptor_frame, self.scaler)
        fingerprint_frame = pd.DataFrame([morgan_fingerprint(smiles) for smiles in smiles_list], index=descriptor_frame.index)
        return pd.concat([descriptor_frame.reset_index(drop=True), fingerprint_frame.reset_index(drop=True)], axis=1)

