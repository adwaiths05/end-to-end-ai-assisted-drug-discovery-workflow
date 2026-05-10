from __future__ import annotations

from fastapi import APIRouter, File, UploadFile
from pathlib import Path
import csv
import io

from pydantic import BaseModel

from app.docking.docking_service import DockingService
from app.schemas import (
    DockingRequest,
    DockingResponse,
    DockingValidationResponse,
    DockingStats,
    InteractionAnalysisResponse,
    Interaction,
    ConsensusRankResponse,
    ConsensusRanked,
    PosesResponse,
    PoseDetails,
    VisualizationResponse,
    VisualizationExport,
)

router = APIRouter(prefix="/docking", tags=["docking"])


# ── Input Options ──────────────────────────────────────────────────
class InputOptionsResponse(BaseModel):
    """Available input options for docking."""
    options: dict


@router.get("/input-options", response_model=InputOptionsResponse)
def get_input_options():
    """Get available input format options for docking."""
    return InputOptionsResponse(
        options={
            "smiles_textarea": {
                "type": "textarea",
                "label": "SMILES Input",
                "placeholder": "Enter one SMILES string per line\nExample:\nCC(=O)Oc1ccccc1C(=O)O\nC1=CC=CC=C1",
                "description": "Paste SMILES strings directly, one per line",
                "accept": "text/plain",
            },
            "csv_upload": {
                "type": "file",
                "label": "CSV Upload",
                "accept": ".csv",
                "description": "Upload CSV file with columns: compound_id, smiles",
                "template": "compound_id,smiles\nASPIRIN,CC(=O)Oc1ccccc1C(=O)O\nBENZENE,c1ccccc1",
            },
        }
    )

    """Parse SMILES input from textarea or CSV.
    
    Returns:
        Tuple of (smiles_list, compound_ids)
    """
    if csv_format:
        # Parse CSV format
        reader = csv.DictReader(io.StringIO(content))
        smiles_list = []
        compound_ids = []
        
        for row in reader:
            if 'smiles' in row:
                smiles_list.append(row['smiles'].strip())
                compound_ids.append(row.get('compound_id', f'lig_{len(smiles_list)-1:03d}'))
        
        return smiles_list, compound_ids if compound_ids else None
    else:
        # Parse textarea format (one SMILES per line)
        smiles_list = [line.strip() for line in content.split('\n') if line.strip()]
        return smiles_list, None


@router.post("/run", response_model=DockingResponse)
def run_docking(request: DockingRequest):
    """Run molecular docking on provided SMILES."""
    from app.docking.docking_config import DockingConfig
    
    # Override defaults if specified in request
    config_overrides = {}
    if request.box_center:
        config_overrides["box_center"] = request.box_center
    if request.box_size:
        config_overrides["box_size"] = request.box_size
    if request.exhaustiveness:
        config_overrides["exhaustiveness"] = request.exhaustiveness
    if request.poses:
        config_overrides["n_poses"] = request.poses
        
    config = DockingConfig(**config_overrides)
    service = DockingService(config=config)
    
    try:
        rows = service.dock_smiles(request.smiles, predictions=request.predicted_pic50)
    except Exception as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    return DockingResponse(status="success", count=len(rows), results=rows)


@router.post("/upload-smiles", response_model=DockingResponse)
def upload_smiles(file: UploadFile = File(...)):
    """Upload SMILES from file (textarea or CSV export)."""
    content = file.file.read().decode('utf-8')
    
    # Detect format
    is_csv = file.filename.endswith('.csv') if file.filename else False
    smiles_list, compound_ids = parse_smiles_input(content, csv_format=is_csv)
    
    if not smiles_list:
        return DockingResponse(status="error", count=0, results=[])
    
    service = DockingService()
    try:
        rows = service.dock_smiles(smiles_list)
    except Exception as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})

    return DockingResponse(status="success", count=len(rows), results=rows)


@router.post("/validate-results", response_model=DockingValidationResponse)
def validate_results(request: DockingRequest):
    """Validate docking results and return statistics."""
    service = DockingService()
    
    # Run docking first
    try:
        rows = service.dock_smiles(request.smiles, predictions=request.predicted_pic50)
    except Exception as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    
    # Validate results
    validation = service.validate_results(rows)
    
    return DockingValidationResponse(
        status="success",
        valid=validation["valid"],
        stats=DockingStats(**validation["stats"]),
        failed_molecules=validation["failed_molecules"],
    )


@router.post("/interactions", response_model=InteractionAnalysisResponse)
def analyze_interactions(request: DockingRequest):
    """Analyze protein-ligand interactions from docked poses."""
    service = DockingService()
    
    # Run docking first
    try:
        docking_results = service.dock_smiles(request.smiles, predictions=request.predicted_pic50)
    except Exception as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    
    # Analyze interactions
    interactions_data = service.analyze_interactions(docking_results)
    
    interactions = [
        Interaction(
            ligand_id=inter["ligand_id"],
            smiles=inter["smiles"],
            affinity=inter["affinity"],
            n_hbonds=inter["n_hbonds"],
            n_contacts=inter["n_contacts"],
            key_residues=inter["key_residues"],
            hbonds=inter["hbonds"],
            top_contacts=inter["top_contacts"],
        )
        for inter in interactions_data
    ]
    
    return InteractionAnalysisResponse(
        status="success",
        receptor_id="EGFR",  # TODO: use from config
        interactions=interactions,
        summary={"total": len(interactions), "analyzed": len(interactions)},
    )


@router.post("/consensus-rank", response_model=ConsensusRankResponse)
def consensus_ranking(
    request: DockingRequest,
    ml_weight: float = 0.5,
):
    """Rank docking results by consensus with ML predictions."""
    service = DockingService()
    try:
        # Run docking
        docking_results = service.dock_smiles(request.smiles, predictions=request.predicted_pic50)
    except Exception as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    
    # Prepare ML predictions if provided
    ml_predictions = None
    if request.predicted_pic50:
        ml_predictions = [
            {"smiles": r["smiles"], "predicted_pic50": r["predicted_pic50"]}
            for r in docking_results
            if r.get("predicted_pic50") is not None
        ]
    
    # Rank by consensus
    ranked = service.rank_by_consensus(docking_results, ml_predictions=ml_predictions, ml_weight=ml_weight)
    
    consensus_ligands = [
        ConsensusRanked(
            rank=r["rank"],
            ligand_id=r["ligand_id"],
            smiles=r["smiles"],
            predicted_pic50=r["predicted_pic50"],
            docking_affinity=r["docking_affinity"],
            ml_rank=r["ml_rank"],
            docking_rank=r["docking_rank"],
            consensus_score=r["consensus_score"],
        )
        for r in ranked
    ]
    
    return ConsensusRankResponse(status="success", total=len(ranked), ranked_ligands=consensus_ligands)


@router.get("/results/{job_id}/poses", response_model=PosesResponse)
def get_poses(job_id: str):
    """Retrieve pose details for a docking job."""
    # TODO: Implement job tracking/storage
    # This is a placeholder that would retrieve from database/cache
    return PosesResponse(
        status="success",
        job_id=job_id,
        total_ligands=0,
        pose_details=[],
    )


@router.post("/visualize", response_model=VisualizationResponse)
def export_visualization(
    request: DockingRequest,
    export_format: VisualizationExport,
):
    """Generate visualization exports (PyMOL, HTML, JSON)."""
    service = DockingService()
    try:
        # Run docking
        docking_results = service.dock_smiles(request.smiles, predictions=request.predicted_pic50)
    except Exception as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    
    # Analyze interactions if requested
    interactions = None
    if export_format.include_interactions:
        interactions = service.analyze_interactions(docking_results)
    
    # Get consensus ranking
    ml_predictions = None
    if request.predicted_pic50:
        ml_predictions = [
            {"smiles": r["smiles"], "predicted_pic50": r["predicted_pic50"]}
            for r in docking_results
            if r.get("predicted_pic50") is not None
        ]
    
    consensus_ranks = service.rank_by_consensus(docking_results, ml_predictions=ml_predictions)
    
    # Export visualizations
    exports = service.export_visualization(
        docking_results,
        interactions=interactions,
        consensus_ranks=consensus_ranks,
        format=export_format.format,
    )
    
    output_file = exports.get(export_format.format, {}).get("path")
    
    return VisualizationResponse(
        status="success",
        format=export_format.format,
        output_file=output_file,
        summary={"exported_formats": list(exports.keys())},
    )

