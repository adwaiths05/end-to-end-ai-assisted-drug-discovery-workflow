from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import Descriptors


DESC_NAMES = [name for name, _ in Descriptors._descList]


def calculate_descriptors(smiles: str) -> dict[str, float]:
    mol = Chem.MolFromSmiles(smiles)
    values: dict[str, float] = {}
    for name, func in Descriptors._descList:
        try:
            values[name] = float(func(mol)) if mol is not None else 0.0
        except Exception:
            values[name] = 0.0
    return values

