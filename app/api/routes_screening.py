from __future__ import annotations

from fastapi import APIRouter, File, UploadFile, Depends, Form
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud
from app.api.deps import get_current_user
from rdkit import Chem
from rdkit.Chem import Descriptors
import csv
from io import StringIO

from app.inference.screening_service import ScreeningService
from app.schemas import (
    ScreeningRequest,
    ScreeningResponse,
    InputOptions,
    ModelInfo,
    ValidationResponse,
    ValidationResult,
    TopHitsResponse,
    FilterStatistics,
)
from app.ensemble.hybrid_ensemble import resolve_ensemble_mode
from app.validation.input_parsing import parse_csv_text, parse_smiles_lines

def _lipinski_filter(smiles: str) -> tuple[bool, dict]:
    """Check if a molecule satisfies Lipinski's Rule of Five."""
    try:
        mol = Chem.MolFromSmiles(smiles)
        if not mol:
            return False, {}
        
        mw = Descriptors.MolWt(mol)
        logp = Descriptors.MolLogP(mol)
        hbd = Descriptors.NumHDonors(mol)
        hba = Descriptors.NumHAcceptors(mol)
        
        # Rule of Five
        mw_ok = mw <= 500
        logp_ok = logp <= 5
        hbd_ok = hbd <= 5
        hba_ok = hba <= 10
        
        passed = mw_ok and logp_ok and hbd_ok and hba_ok
        return passed, {"mw": mw, "logp": logp, "hbd": hbd, "hba": hba}
    except Exception:
        return False, {}

router = APIRouter(prefix="/screening", tags=["screening"])


# ── Input Format & Configuration ───────────────────────────────────

@router.get("/input-options", response_model=InputOptions)
def get_input_options():
    """Get available input format options for virtual screening."""
    return InputOptions()


@router.get("/models/info", response_model=ModelInfo)
def get_model_info():
    """Get information about active ensemble configuration."""
    service = ScreeningService()
    active_mode = resolve_ensemble_mode(service.artifacts)
    return ModelInfo(
        status="success",
        active_ensemble=active_mode,
    )


# ── Input Validation ───────────────────────────────────────────────

def _lipinski_filter(smiles: str) -> tuple[bool, str | None]:
    """Check if compound passes Lipinski's rule of 5."""
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        return False, "Invalid SMILES"
    
    mw = Descriptors.MolWt(mol)
    logp = Descriptors.MolLogP(mol)
    hbd = Descriptors.NumHDonors(mol)
    hba = Descriptors.NumHAcceptors(mol)
    
    failures = []
    if mw > 500:
        failures.append(f"MW={mw:.1f} > 500")
    if logp > 5:
        failures.append(f"LogP={logp:.1f} > 5")
    if hbd > 5:
        failures.append(f"HBD={hbd} > 5")
    if hba > 10:
        failures.append(f"HBA={hba} > 10")
    
    if failures:
        return False, "; ".join(failures)
    return True, None


@router.post("/validate-smiles", response_model=ValidationResponse)
def validate_smiles(request: ScreeningRequest):
    """Validate SMILES strings before screening."""
    results = []
    valid_count = 0
    
    for smi in request.smiles:
        mol = Chem.MolFromSmiles(smi)
        if mol is None:
            results.append(ValidationResult(smiles=smi, valid=False, reason="Invalid SMILES"))
        else:
            valid, reason = _lipinski_filter(smi)
            results.append(
                ValidationResult(
                    smiles=smi,
                    valid=valid,
                    reason=reason,
                    can_standardize=True,
                )
            )
            if valid:
                valid_count += 1
    
    return ValidationResponse(
        status="success",
        total_compounds=len(request.smiles),
        valid_count=valid_count,
        invalid_count=len(request.smiles) - valid_count,
        results=results,
    )


# ── Core Screening ─────────────────────────────────────────────────

@router.post("/smiles", response_model=ScreeningResponse)
def screen_smiles(request: ScreeningRequest):
    service = ScreeningService()
    try:
        results = service.screen_smiles(request.smiles, top_n=request.top_n)
    except Exception as exc:
        # Return a clear error message for caller
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    active_mode = resolve_ensemble_mode(service.artifacts)
    return ScreeningResponse(status="success", active_ensemble=active_mode, count=len(results), results=results)



@router.post("/upload", response_model=ScreeningResponse)
async def upload_screening_file(
    file: UploadFile = File(...), 
    top_n: int | None = Form(None),
    filter_lipinski: bool = Form(False),
    db: Session = Depends(get_db), 
    current_user = Depends(get_current_user)
):
    content = (await file.read()).decode("utf-8")
    
    # Auto-detect format
    smiles = []
    compound_ids = None
    
    if file.filename and file.filename.lower().endswith(".csv"):
        # Parse CSV format
        reader = csv.DictReader(StringIO(content))
        smiles = []
        compound_ids = []
        
        for row in reader:
            if 'smiles' in row:
                smiles.append(row['smiles'].strip())
                compound_ids.append(row.get('compound_id', f'lig_{len(smiles)-1:03d}'))
        
        compound_ids = compound_ids if compound_ids else None
    else:
        # Parse textarea format
        smiles = parse_smiles_lines(content)
    
    service = ScreeningService()
    try:
        results = service.screen_smiles(smiles, top_n=None, compound_ids=compound_ids)
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    
    # Apply filters using pre-calculated metadata
    if filter_lipinski:
        results = [
            r for r in results 
            if r.get("metadata", {}).get("mw", 0) <= 500 and 
               r.get("metadata", {}).get("logp", 0) <= 5 and 
               r.get("metadata", {}).get("hbd", 0) <= 5 and 
               r.get("metadata", {}).get("hba", 0) <= 10
        ]
    # No else needed: metadata is already collected by ScreeningService
    
    # Sort and slice
    results = sorted(results, key=lambda x: x.get("predicted_pic50") or 0, reverse=True)
    if top_n:
        results = results[:top_n]
    
    active_mode = resolve_ensemble_mode(service.artifacts)
    
    # Save to database, but do not fail the upload if persistence is unavailable.
    try:
        crud.create_screening_run(db, current_user.id, results, active_mode)
    except Exception as exc:
        from logging import getLogger

        getLogger(__name__).exception("Failed to persist uploaded screening results: %s", exc)

    return ScreeningResponse(status="success", active_ensemble=active_mode, count=len(results), results=results)


# ── Advanced Screening with Filtering ──────────────────────────────

@router.post("/batch", response_model=ScreeningResponse)
def screen_batch(request: ScreeningRequest, db: Session = Depends(get_db), current_user = Depends(get_current_user)):
    """Screen compounds with optional filtering (Lipinski, uncertainty, confidence)."""
    service = ScreeningService()
    try:
        results = service.screen_smiles(request.smiles, top_n=None, compound_ids=request.compound_ids)
    except Exception as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    
    # Apply Lipinski filter if requested (using pre-calculated metadata)
    if request.filter_lipinski:
        results = [
            r for r in results 
            if r.get("metadata", {}).get("mw", 0) <= 500 and 
               r.get("metadata", {}).get("logp", 0) <= 5 and 
               r.get("metadata", {}).get("hbd", 0) <= 5 and 
               r.get("metadata", {}).get("hba", 0) <= 10
        ]
    
    # Apply uncertainty threshold if provided
    if request.uncertainty_threshold is not None:
        results = [
            r for r in results
            if r.get("uncertainty") is not None and r.get("uncertainty") <= request.uncertainty_threshold
        ]
    
    # Apply confidence threshold if provided
    if request.min_confidence is not None:
        results = [
            r for r in results
            if r.get("confidence") is not None and r.get("confidence") >= request.min_confidence
        ]
    
    # Sort by predicted pIC50 (descending)
    results = sorted(results, key=lambda x: x.get("predicted_pic50") or 0, reverse=True)
    
    # Apply top_n limit
    if request.top_n:
        results = results[:request.top_n]
    
    active_mode = resolve_ensemble_mode(service.artifacts)
    
    # Save to database, but do not fail the request if persistence is unavailable.
    try:
        crud.create_screening_run(db, current_user.id, results, active_mode)
    except Exception as exc:
        from logging import getLogger

        getLogger(__name__).exception("Failed to persist batch screening results: %s", exc)

    return ScreeningResponse(status="success", active_ensemble=active_mode, count=len(results), results=results)


@router.post("/top-hits", response_model=TopHitsResponse)
def get_top_hits(request: ScreeningRequest):
    """Get top-N compounds with automatic filtering and ranking."""
    service = ScreeningService()
    try:
        initial_results = service.screen_smiles(request.smiles, top_n=None)
    except Exception as exc:
        from fastapi import HTTPException

        raise HTTPException(status_code=500, detail={"status": "failed", "message": str(exc)})
    
    # Track filtering statistics
    lipinski_failed = 0
    uncertainty_filtered = 0
    confidence_filtered = 0
    
    # Apply default filters
    results = initial_results[:]
    
    # Filter by Lipinski (default: True for top-hits)
    results = [
        r for r in results
        if _lipinski_filter(r.smiles)[0]
    ]
    lipinski_failed = len(initial_results) - len(results)
    
    # Filter by uncertainty (default: 75th percentile)
    uncertainties = [r.uncertainty for r in results if r.uncertainty is not None]
    if uncertainties:
        uncertainty_threshold = request.uncertainty_threshold or (
            sorted(uncertainties)[int(len(uncertainties) * 0.75)]
        )
        initial_uncertain = len(results)
        results = [
            r for r in results
            if r.uncertainty is not None and r.uncertainty <= uncertainty_threshold
        ]
        uncertainty_filtered = initial_uncertain - len(results)
    
    # Filter by confidence if specified
    if request.min_confidence:
        initial_confident = len(results)
        results = [
            r for r in results
            if r.get("confidence") is not None and r.get("confidence") >= request.min_confidence
        ]
        confidence_filtered = initial_confident - len(results)
    
    # Sort by predicted pIC50 (descending)
    results = sorted(results, key=lambda x: x.get("predicted_pic50") or 0, reverse=True)
    
    # Get top-N (default: 50)
    top_n = request.top_n or 50
    results = results[:top_n]
    
    # Build statistics
    stats = FilterStatistics(
        total_screened=len(initial_results),
        passed_all_filters=len(results),
        lipinski_failed=lipinski_failed,
        uncertainty_filtered=uncertainty_filtered,
        confidence_filtered=confidence_filtered,
    )
    
    return TopHitsResponse(
        status="success",
        total_screened=len(initial_results),
        hits_returned=len(results),
        filters_applied={
            "lipinski": True,
            "uncertainty_threshold": uncertainty_threshold if uncertainties else None,
            "min_confidence": request.min_confidence,
        },
        statistics=stats,
        top_hits=results,
    )

