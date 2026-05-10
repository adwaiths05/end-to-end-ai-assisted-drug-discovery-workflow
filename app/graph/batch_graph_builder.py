from __future__ import annotations

from collections.abc import Sequence

from app.graph.smiles_to_graph import smiles_to_graph


def build_graphs(smiles_list: Sequence[str], labels: Sequence[float] | None = None):
    graphs = []
    valid_indices = []
    for index, smiles in enumerate(smiles_list):
        label = labels[index] if labels is not None and index < len(labels) else None
        graph = smiles_to_graph(smiles, label=label)
        if graph is not None:
            graphs.append(graph)
            valid_indices.append(index)
    return graphs, valid_indices

