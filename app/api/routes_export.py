from __future__ import annotations

from fastapi import APIRouter

from app.export.csv_exporter import export_csv
from app.export.json_exporter import export_json
from app.schemas import ExportRequest
from app.utils.file_utils import safe_filename
from app.config import settings

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/csv")
def export_as_csv(request: ExportRequest):
    from pandas import DataFrame

    path = settings.output_dir / f"{safe_filename(request.filename)}.csv"
    export_csv(DataFrame(request.records), path)
    return {"status": "success", "path": str(path)}


@router.post("/json")
def export_as_json(request: ExportRequest):
    path = settings.output_dir / f"{safe_filename(request.filename)}.json"
    export_json(request.records, path)
    return {"status": "success", "path": str(path)}

