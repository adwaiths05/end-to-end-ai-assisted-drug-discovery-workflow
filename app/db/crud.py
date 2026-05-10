from sqlalchemy.orm import Session
from app.db.models import User, ScreeningRun, CompoundResult, DockingResult, ModelPerformance, UserFeedback
from app.core import security

def get_user_by_email(db: Session, email: str):
    return db.query(User).filter(User.email == email).first()

def create_user(db: Session, user: dict):
    hashed_password = security.get_password_hash(user["password"])
    db_user = User(
        name=user["name"],
        email=user["email"],
        password_hash=hashed_password
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_platform_stats(db: Session):
    total_runs = db.query(ScreeningRun).count()
    total_compounds = db.query(CompoundResult).count()
    
    # Calculate avg pic50 across all compounds
    from sqlalchemy.sql import func
    avg_pic50 = db.query(func.avg(CompoundResult.predicted_pic50)).scalar() or 0.0
    
    return {
        "total_runs": total_runs,
        "total_compounds": total_compounds,
        "avg_pic50": avg_pic50
    }

def get_recent_discoveries(db: Session, limit: int = 3):
    return db.query(CompoundResult).order_by(CompoundResult.predicted_pic50.desc()).limit(limit).all()

def get_user_dashboard_stats(db: Session, user_id: str):
    runs = db.query(ScreeningRun).filter(ScreeningRun.user_id == user_id).all()
    total_runs = len(runs)
    total_compounds = sum(r.valid_compounds for r in runs if r.valid_compounds)
    from sqlalchemy.sql import func
    best_pic50 = db.query(func.max(CompoundResult.predicted_pic50)).join(ScreeningRun).filter(ScreeningRun.user_id == user_id).scalar() or 0.0
    
    avg_conf = db.query(func.avg(ScreeningRun.avg_confidence)).filter(ScreeningRun.user_id == user_id).scalar() or 0.0
    
    return {
        "total_runs": total_runs,
        "total_compounds": total_compounds,
        "best_pic50": best_pic50,
        "avg_confidence": avg_conf
    }
def create_screening_run(db: Session, user_id: str, results: list[dict], ensemble_mode: str):
    import uuid
    run_id = str(uuid.uuid4())
    
    valid_results = [r for r in results if r.get("valid")]
    avg_pic50 = sum(r.get("predicted_pic50") or 0 for r in valid_results) / len(valid_results) if valid_results else 0
    avg_conf = sum(r.get("confidence") or 0 for r in valid_results) / len(valid_results) if valid_results else 0
    
    db_run = ScreeningRun(
        id=run_id,
        user_id=user_id,
        active_ensemble=ensemble_mode,
        total_compounds=len(results),
        valid_compounds=len(valid_results),
        avg_pic50=avg_pic50,
        avg_confidence=avg_conf
    )
    db.add(db_run)
    
    # Bulk insert compounds
    for r in results:
        comp = CompoundResult(
            id=str(uuid.uuid4()),
            run_id=run_id,
            smiles=r["smiles"],
            compound_id=r.get("compound_id"),
            predicted_pic50=r.get("predicted_pic50"),
            confidence=r.get("confidence"),
            uncertainty=r.get("uncertainty"),
            agreement=r.get("agreement"),
            model_predictions=r.get("model_predictions", {}),
            mol_properties=r.get("mol_properties", {})
        )
        db.add(comp)
    
    db.commit()
    db.refresh(db_run)
    return db_run
