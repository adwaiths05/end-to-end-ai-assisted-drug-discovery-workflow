from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db import crud
from app.api.deps import get_current_user

router = APIRouter(prefix="/api/analytics", tags=["analytics"])

@router.get("/summary")
def get_platform_summary(db: Session = Depends(get_db)):
    """Returns platform-wide statistics for the landing page."""
    stats = crud.get_platform_stats(db)
    recent = crud.get_recent_discoveries(db, limit=3)
    return {
        "stats": stats,
        "recent_discoveries": [
            {
                "id": r.id,
                "compound_id": r.compound_id,
                "pic50": r.predicted_pic50,
                "created_at": r.created_at
            } for r in recent
        ]
    }

@router.get("/dashboard")
def get_user_dashboard(current_user = Depends(get_current_user), db: Session = Depends(get_db)):
    """Returns personal statistics and recent runs for the dashboard."""
    stats = crud.get_user_dashboard_stats(db, current_user.id)
    
    # Get user's recent runs
    from app.db.models import ScreeningRun
    recent_runs = db.query(ScreeningRun).filter(ScreeningRun.user_id == current_user.id).order_by(ScreeningRun.created_at.desc()).limit(5).all()
    
    return {
        "stats": stats,
        "recent_runs": [
            {
                "id": run.id,
                "status": run.status,
                "compounds": run.total_compounds,
                "ensemble": run.active_ensemble,
                "avg_pic50": run.avg_pic50,
                "created_at": run.created_at
            } for run in recent_runs
        ]
    }
