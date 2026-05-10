import uuid
from datetime import datetime
from sqlalchemy import Column, String, Float, Integer, Boolean, DateTime, JSON, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="researcher")
    created_at = Column(DateTime, default=datetime.utcnow)
    last_active = Column(DateTime, nullable=True)

    screening_runs = relationship("ScreeningRun", back_populates="user")
    feedback = relationship("UserFeedback", back_populates="user")

class ScreeningRun(Base):
    __tablename__ = "screening_runs"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, ForeignKey("users.id"), nullable=True)
    source_name = Column(String, nullable=True)
    total_compounds = Column(Integer)
    valid_compounds = Column(Integer)
    active_ensemble = Column(String)
    avg_pic50 = Column(Float, nullable=True)
    avg_confidence = Column(Float, nullable=True)
    lipinski_filter = Column(Boolean, default=False)
    status = Column(String, default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="screening_runs")
    compounds = relationship("CompoundResult", back_populates="run")
    docking = relationship("DockingResult", back_populates="run")
    performance = relationship("ModelPerformance", back_populates="run", uselist=False)

class CompoundResult(Base):
    __tablename__ = "compound_results"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("screening_runs.id"), nullable=False)
    compound_id = Column(String, nullable=True)
    smiles = Column(Text, nullable=False)
    canonical_smiles = Column(Text, nullable=True)
    predicted_pic50 = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    uncertainty = Column(Float, nullable=True)
    agreement = Column(Float, nullable=True)
    rank = Column(Integer, nullable=True)
    model_predictions = Column(JSON, default=dict)
    mol_properties = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ScreeningRun", back_populates="compounds")
    feedback = relationship("UserFeedback", back_populates="compound", uselist=False)

class DockingResult(Base):
    __tablename__ = "docking_results"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("screening_runs.id"), nullable=False)
    compound_id = Column(String, nullable=True)
    smiles = Column(Text, nullable=False)
    docking_affinity = Column(Float, nullable=True)
    consensus_score = Column(Float, nullable=True)
    pose_count = Column(Integer, nullable=True)
    pose_energies = Column(JSON, default=list)
    interactions = Column(JSON, default=dict)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ScreeningRun", back_populates="docking")

class ModelPerformance(Base):
    __tablename__ = "model_performance"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    run_id = Column(String, ForeignKey("screening_runs.id"), nullable=False)
    ensemble_mode = Column(String)
    rf_avg = Column(Float, nullable=True)
    xgb_avg = Column(Float, nullable=True)
    mpnn_avg = Column(Float, nullable=True)
    gin_avg = Column(Float, nullable=True)
    meta_avg = Column(Float, nullable=True)
    agreement_avg = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    run = relationship("ScreeningRun", back_populates="performance")

class UserFeedback(Base):
    __tablename__ = "user_feedback"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    compound_id = Column(String, ForeignKey("compound_results.id"), nullable=False)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    label = Column(String)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    compound = relationship("CompoundResult", back_populates="feedback")
    user = relationship("User", back_populates="feedback")
