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
