from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class MoleculeInput(BaseModel):
    """Support both SMILES textarea and CSV upload formats."""
    smiles_list: list[str] = Field(default_factory=list, description="SMILES strings (one per line)")
    compound_ids: list[str] | None = Field(default=None, description="Optional compound IDs from CSV")
    predictions: list[float] | None = Field(default=None, description="Optional predicted values (pIC50, etc.)")


class ScreeningRequest(BaseModel):
    """Input for virtual screening with optional compound tracking and filtering."""
    smiles: list[str] = Field(default_factory=list, description="SMILES strings")
    compound_ids: list[str] | None = Field(default=None, description="Optional compound identifiers")
    source_name: str | None = Field(default=None, description="Optional data source name")
    top_n: int | None = Field(default=None, description="Return top-N results")
    # Filter options (for batch screening)
    filter_lipinski: bool = Field(default=False, description="Apply Lipinski's rule of 5")
    uncertainty_threshold: float | None = Field(default=None, description="Max uncertainty (std of ensemble)")
    min_confidence: float | None = Field(default=None, description="Min confidence threshold")


class DockingRequest(BaseModel):
    smiles: list[str] = Field(default_factory=list)
    predicted_pic50: list[float] | None = None
    compound_ids: list[str] | None = None
    top_n: int | None = None
    box_center: tuple[float, float, float] | None = None
    box_size: tuple[float, float, float] | None = None
    exhaustiveness: int | None = None
    poses: int | None = None


class ExportRequest(BaseModel):
    records: list[dict[str, Any]]
    filename: str = "results"


class MoleculePrediction(BaseModel):
    compound_id: str | None = None
    smiles: str
    canonical_smiles: str | None = None
    valid: bool = True
    standardized: bool = True
    predicted_pic50: float | None = None
    confidence: float | None = None
    uncertainty: float | None = None
    agreement: float | None = None
    docking_affinity: float | None = None
    consensus_score: float | None = None
    rank: int | None = None
    model_predictions: dict[str, float] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScreeningResponse(BaseModel):
    status: str
    active_ensemble: str
    count: int
    results: list[MoleculePrediction]


class DockingResult(BaseModel):
    compound_id: str | None = None
    smiles: str
    affinity: float | None = None
    pose_count: int | None = None
    status: str
    details: dict[str, Any] = Field(default_factory=dict)


class DockingResponse(BaseModel):
    status: str
    count: int
    results: list[DockingResult]


# ── POST /docking/validate-results ────────────────────────────────
class DockingStats(BaseModel):
    total_molecules: int
    succeeded: int
    failed: int
    success_rate: float
    affinity_mean: float | None = None
    affinity_std: float | None = None
    affinity_min: float | None = None
    affinity_max: float | None = None


class DockingValidationResponse(BaseModel):
    status: str
    valid: bool
    stats: DockingStats
    failed_molecules: list[dict[str, Any]] = Field(default_factory=list)


# ── POST /docking/interactions ────────────────────────────────────
class HBond(BaseModel):
    ligand_atom: str
    receptor_residue: str
    receptor_atom: str
    distance: float


class Interaction(BaseModel):
    ligand_id: str
    smiles: str
    affinity: float
    n_hbonds: int
    n_contacts: int
    key_residues: list[str] = Field(default_factory=list)
    hbonds: list[HBond] = Field(default_factory=list)
    top_contacts: dict[str, float] = Field(default_factory=dict)


class InteractionAnalysisResponse(BaseModel):
    status: str
    receptor_id: str
    interactions: list[Interaction] = Field(default_factory=list)
    summary: dict[str, Any] = Field(default_factory=dict)


# ── POST /docking/consensus-rank ──────────────────────────────────
class ConsensusRanked(BaseModel):
    rank: int
    ligand_id: str
    smiles: str
    predicted_pic50: float | None = None
    docking_affinity: float | None = None
    ml_rank: int | None = None
    docking_rank: int | None = None
    consensus_score: float


class ConsensusRankResponse(BaseModel):
    status: str
    total: int
    ranked_ligands: list[ConsensusRanked] = Field(default_factory=list)


# ── GET /docking/results/{job_id}/poses ───────────────────────────
class PoseEnergy(BaseModel):
    pose_id: int
    affinity: float
    rmsd_lb: float | None = None
    rmsd_ub: float | None = None


class PoseDetails(BaseModel):
    ligand_id: str
    smiles: str
    best_affinity: float
    poses: list[PoseEnergy] = Field(default_factory=list)
    pose_file: str | None = None


class PosesResponse(BaseModel):
    status: str
    job_id: str
    total_ligands: int
    pose_details: list[PoseDetails] = Field(default_factory=list)


# ── POST /docking/visualize ───────────────────────────────────────
class VisualizationExport(BaseModel):
    format: str = Field(default="pymol", description="pymol, pml, or summary")
    top_n: int = Field(default=5, description="Top N hits to include")
    include_interactions: bool = Field(default=True, description="Include H-bond/contact analysis")


class VisualizationResponse(BaseModel):
    status: str
    format: str
    output_file: str | None = None
    script_content: str | None = None
    summary: dict[str, Any] = Field(default_factory=dict)


# ── SCREENING INPUT/OUTPUT MODELS ─────────────────────────────────

class InputOptions(BaseModel):
    """Available input format options for virtual screening."""
    options: dict = Field(
        default={
            "smiles_textarea": {
                "type": "textarea",
                "label": "SMILES Input",
                "placeholder": "Enter one SMILES string per line\nExample:\nCC(=O)Oc1ccccc1C(=O)O\nC1=CC=CC=C1",
                "description": "Paste SMILES strings directly, one per line",
            },
            "csv_upload": {
                "type": "file",
                "label": "CSV Upload",
                "accept": ".csv",
                "description": "Upload CSV file with columns: compound_id (optional), smiles",
                "template": "compound_id,smiles\nASPIRIN,CC(=O)Oc1ccccc1C(=O)O\nBENZENE,c1ccccc1",
            },
        }
    )


class ModelInfo(BaseModel):
    """Information about active ensemble configuration."""
    status: str
    active_ensemble: str
    base_models: list[str] = Field(default=["RF", "XGB", "MPNN", "GIN"])
    meta_learner: str = Field(default="Ridge")
    feature_sets: dict[str, int] = Field(
        default={
            "descriptors": 200,
            "fingerprints": 2048,
            "image_embeddings": 512,
        }
    )
    total_features: int = Field(default=2760)
    model_weights: dict[str, float] = Field(
        default={"RF": 0.25, "XGB": 0.25, "MPNN": 0.25, "GIN": 0.25}
    )


class ValidationResult(BaseModel):
    """Result of SMILES validation."""
    smiles: str
    valid: bool
    reason: str | None = None
    can_standardize: bool = False


class ValidationResponse(BaseModel):
    """Response from SMILES validation endpoint."""
    status: str
    total_compounds: int
    valid_count: int
    invalid_count: int
    results: list[ValidationResult] = Field(default_factory=list)


class FilterStatistics(BaseModel):
    """Statistics from filtering operation."""
    total_screened: int
    passed_all_filters: int
    lipinski_failed: int
    uncertainty_filtered: int
    confidence_filtered: int


class TopHitsResponse(BaseModel):
    """Response for top-hits endpoint with filtering applied."""
    status: str
    total_screened: int
    hits_returned: int
    filters_applied: dict[str, bool | float] = Field(default_factory=dict)
    statistics: FilterStatistics
    top_hits: list[MoleculePrediction] = Field(default_factory=list)

