from __future__ import annotations

from rdkit import Chem


def is_valid_smiles(smiles: str | None) -> bool:
    if not smiles or not isinstance(smiles, str):
        return False
    return Chem.MolFromSmiles(smiles) is not None


def canonicalize_smiles(smiles: str) -> str | None:
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return None
    return Chem.MolToSmiles(mol, canonical=True)

