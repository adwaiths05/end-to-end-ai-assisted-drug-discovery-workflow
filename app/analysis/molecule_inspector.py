from __future__ import annotations

from rdkit import Chem
from rdkit.Chem import Descriptors


def inspect_molecule(smiles: str, predictions: dict | None = None) -> dict:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return {"smiles": smiles, "valid": False}
    data = {
        "smiles": smiles,
        "valid": True,
        "molecular_weight": float(Descriptors.MolWt(mol)),
        "logp": float(Descriptors.MolLogP(mol)),
        "hbd": float(Descriptors.NumHDonors(mol)),
        "hba": float(Descriptors.NumHAcceptors(mol)),
        "rotatable_bonds": float(Descriptors.NumRotatableBonds(mol)),
        "tpsa": float(Descriptors.TPSA(mol)),
    }
    if predictions:
        data.update(predictions)
    return data

