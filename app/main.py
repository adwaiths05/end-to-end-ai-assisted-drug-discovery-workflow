from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.routes_analysis import router as analysis_router
from app.api.routes_docking import router as docking_router
from app.api.routes_export import router as export_router
from app.api.routes_screening import router as screening_router
from app.api.routes_auth import router as auth_router
from app.api.routes_analytics import router as analytics_router
from app.config import settings
from app.logging_config import configure_logging
from app.models.artifact_loader import load_artifacts

configure_logging()
app = FastAPI(title="EGFR Virtual Screening Backend", version="0.1.0")

# Allow requests from the Next.js frontend (dev: 3000, prod: set via env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event() -> None:
    load_artifacts()

@app.get("/health")
def health():
    artifacts = load_artifacts()
    return {"status": "ok", "active_models": artifacts.active_models}

app.include_router(auth_router)
app.include_router(analytics_router)
app.include_router(screening_router)
app.include_router(docking_router)
app.include_router(export_router)
app.include_router(analysis_router)

# Serve the data directory so the frontend can fetch the generated PDBQT files for 3D visualization
app.mount("/data", StaticFiles(directory=settings.data_dir), name="data")

