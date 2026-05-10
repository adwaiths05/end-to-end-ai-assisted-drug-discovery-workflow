from __future__ import annotations

from rdkit import Chem


BOND_TYPES = [Chem.BondType.SINGLE, Chem.BondType.DOUBLE, Chem.BondType.TRIPLE, Chem.BondType.AROMATIC]
STEREO_TYPES = [Chem.BondStereo.STEREONONE, Chem.BondStereo.STEREOZ, Chem.BondStereo.STEREOE]


def one_hot(value, choices) -> list[int]:
    return [int(value == choice) for choice in choices]


def bond_features(bond: Chem.Bond) -> list[float]:
    features: list[float] = []
    features.extend(one_hot(bond.GetBondType(), BOND_TYPES))
    features.extend(one_hot(bond.GetStereo(), STEREO_TYPES))
    features.append(float(bond.IsInRing()))
    features.append(float(bond.GetIsConjugated()))
    return features

