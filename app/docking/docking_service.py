from __future__ import annotations

import logging
from pathlib import Path

from app.config import settings
from app.docking.docking_config import DockingConfig
from app.docking.ligand_preparation import sdf_to_pdbqt, smiles_to_sdf
from app.docking.pdbqt_validation import get_ligand_center_from_pdb, validate_receptor_pdbqt
from app.docking.receptor_preparation import convert_pdb_to_pdbqt, download_receptor_pdb, strip_receptor_pdb
from app.docking.vina_runner import VinaRunner

LOGGER = logging.getLogger(__name__)


class DockingService:
    def __init__(self, config: DockingConfig | None = None) -> None:
        self.config = config or DockingConfig()
        self.work_dir = settings.docking_dir
        self.work_dir.mkdir(parents=True, exist_ok=True)

    def prepare_receptor(self) -> Path:
        raw_pdb = self.work_dir / f"{self.config.receptor_id}.pdb"
        clean_pdb = self.work_dir / f"{self.config.receptor_id}_clean.pdb"
        receptor_pdbqt = self.work_dir / f"{self.config.receptor_id}_receptor.pdbqt"
        download_receptor_pdb(self.config.receptor_pdb_url, raw_pdb)
        strip_receptor_pdb(raw_pdb, clean_pdb)
        try:
            convert_pdb_to_pdbqt(clean_pdb, receptor_pdbqt)
            return receptor_pdbqt
        except Exception:
            LOGGER.warning("Falling back to clean PDB because receptor PDBQT conversion failed")
            return clean_pdb

    def validate_receptor(self, receptor_path: Path) -> bool:
        """Validate receptor PDBQT for docking readiness."""
        result = validate_receptor_pdbqt(receptor_path)
        if not result["valid"]:
            LOGGER.error(f"Receptor validation failed: {result.get('error')}")
            if result.get("warnings"):
                for warning in result["warnings"]:
                    if warning:
                        LOGGER.warning(warning)
            return False
        LOGGER.info(
            f"Receptor validated: {result['atom_count']} atoms, "
            f"{result['hd_count']} HD, {result['acceptor_count']} acceptors"
        )
        return True

    def auto_detect_binding_box(self, pdb_path: Path) -> tuple[float, float, float] | None:
        """Auto-detect binding box center from co-crystallized ligand."""
        center = get_ligand_center_from_pdb(pdb_path)
        if center:
            LOGGER.info(f"Auto-detected binding box center: {center}")
        return center

    def dock_smiles(self, smiles_list: list[str], predictions: list[float] | None = None) -> list[dict]:
        raw_pdb = self.work_dir / f"{self.config.receptor_id}.pdb"
        receptor = self.prepare_receptor()

        if receptor.suffix.lower() != ".pdbqt":
            raise RuntimeError("Docking requires a receptor PDBQT file. Install obabel or provide a receptor PDBQT.")

        # Validate receptor
        if not self.validate_receptor(receptor):
            LOGGER.warning("Receptor validation warnings — proceeding with caution")

        # Auto-detect binding box if not provided
        box_center = self.config.box_center
        if not box_center or box_center == (0.0, 0.0, 0.0):
            auto_center = self.auto_detect_binding_box(raw_pdb)
            if auto_center:
                box_center = auto_center

        runner = VinaRunner(
            receptor, box_center, self.config.box_size, self.config.exhaustiveness, self.config.n_poses
        )
        rows = []

        for index, smiles in enumerate(smiles_list):
            sdf_path = self.work_dir / f"ligand_{index}.sdf"
            pdbqt_path = self.work_dir / f"ligand_{index}.pdbqt"
            try:
                sdf = smiles_to_sdf(smiles, sdf_path)
                if sdf is None:
                    raise ValueError("invalid smiles")
                sdf_to_pdbqt(sdf, pdbqt_path)
                result = runner.dock(pdbqt_path)
                rows.append(
                    {
                        "smiles": smiles,
                        "predicted_pic50": predictions[index] if predictions and index < len(predictions) else None,
                        "vina_affinity": result.get("best_affinity"),
                        "pose_count": self.config.n_poses,
                        "status": "success",
                        "details": result,
                    }
                )
            except Exception as exc:
                LOGGER.exception("Docking failed for molecule %s", index)
                rows.append(
                    {
                        "smiles": smiles,
                        "predicted_pic50": predictions[index] if predictions and index < len(predictions) else None,
                        "vina_affinity": None,
                        "pose_count": 0,
                        "status": f"failed: {exc}",
                        "details": {},
                    }
                )

        return rows

    def validate_results(self, docking_results: list[dict]) -> dict:
        """Validate and compute statistics on docking results."""
        import numpy as np

        total = len(docking_results)
        succeeded = sum(1 for r in docking_results if r.get("status") == "success")
        failed = total - succeeded

        affinities = [r.get("vina_affinity") for r in docking_results if r.get("vina_affinity") is not None]

        stats = {
            "total_molecules": total,
            "succeeded": succeeded,
            "failed": failed,
            "success_rate": round(succeeded / total, 3) if total > 0 else 0,
            "affinity_mean": round(float(np.mean(affinities)), 3) if affinities else None,
            "affinity_std": round(float(np.std(affinities)), 3) if affinities else None,
            "affinity_min": round(float(np.min(affinities)), 3) if affinities else None,
            "affinity_max": round(float(np.max(affinities)), 3) if affinities else None,
        }

        failed_molecules = [
            {"smiles": r.get("smiles"), "status": r.get("status")} for r in docking_results if r.get("status") != "success"
        ]

        LOGGER.info(f"Docking results: {succeeded}/{total} succeeded, mean affinity: {stats['affinity_mean']}")

        return {
            "valid": succeeded > 0,
            "stats": stats,
            "failed_molecules": failed_molecules,
        }

    def analyze_interactions(self, docking_results: list[dict], receptor_pdbqt: Path | None = None) -> list[dict]:
        """Analyze protein-ligand interactions from docked poses."""
        from app.docking.interaction_analysis import InteractionAnalyzer

        if receptor_pdbqt is None:
            receptor_pdbqt = self.work_dir / f"{self.config.receptor_id}_receptor.pdbqt"

        if not receptor_pdbqt.exists():
            LOGGER.warning(f"Receptor PDBQT not found: {receptor_pdbqt}")
            return []

        analyzer = InteractionAnalyzer(receptor_pdbqt)
        interactions = []

        for result in docking_results:
            if result.get("status") != "success":
                continue

            # Look for pose file
            pose_file = result.get("details", {}).get("pose_file")
            if not pose_file or not Path(pose_file).exists():
                continue

            interaction = analyzer.analyze_pose(
                ligand_id=result.get("name", result.get("smiles", "unknown")),
                smiles=result.get("smiles"),
                affinity=result.get("vina_affinity", 0),
                pose_pdbqt=Path(pose_file),
            )
            interactions.append(interaction)

        LOGGER.info(f"Analyzed interactions for {len(interactions)} poses")
        return interactions

    def rank_by_consensus(
        self, docking_results: list[dict], ml_predictions: list[dict] | None = None, ml_weight: float = 0.5
    ) -> list[dict]:
        """Rank docking results by consensus with ML predictions."""
        from app.docking.consensus_ranking import ConsensusRanker

        ranked = ConsensusRanker.rank(
            docking_results, ml_predictions=ml_predictions, ml_weight=ml_weight, dock_weight=1 - ml_weight
        )

        return [r.to_dict() for r in ranked]

    def export_visualization(
        self,
        docking_results: list[dict],
        interactions: list[dict] | None = None,
        consensus_ranks: list[dict] | None = None,
        format: str = "all",
        output_dir: Path | None = None,
    ) -> dict:
        """Export docking results for visualization."""
        from app.docking.visualization_export import VisualizationExporter

        if output_dir is None:
            output_dir = self.work_dir / "visualizations"
        output_dir.mkdir(parents=True, exist_ok=True)

        clean_pdb = self.work_dir / f"{self.config.receptor_id}_clean.pdb"
        receptor_pdbqt = self.work_dir / f"{self.config.receptor_id}_receptor.pdbqt"

        exporter = VisualizationExporter(clean_pdb, receptor_pdbqt)

        exports = {}

        if format in ["all", "pymol"]:
            pml_path = output_dir / "session_top_poses.pml"
            script = exporter.generate_pymol_script(
                [r for r in docking_results if r.get("status") == "success"][:10],
                output_path=pml_path,
                include_interactions=True,
            )
            exports["pymol"] = {"path": str(pml_path), "generated": True}

        if format in ["all", "html"]:
            html_path = output_dir / "docking_summary.html"
            html = exporter.generate_html_summary(
                interactions or [],
                consensus_ranks=consensus_ranks,
                output_path=html_path,
            )
            exports["html"] = {"path": str(html_path), "generated": True}

        if format in ["all", "json"]:
            json_path = output_dir / "docking_export.json"
            json_str = exporter.generate_json_export(
                docking_results, interactions=interactions, consensus_ranks=consensus_ranks, output_path=json_path
            )
            exports["json"] = {"path": str(json_path), "generated": True}

        LOGGER.info(f"Exported visualizations: {list(exports.keys())}")
        return exports