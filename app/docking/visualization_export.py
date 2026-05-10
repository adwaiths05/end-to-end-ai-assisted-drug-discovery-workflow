from __future__ import annotations

import json
import logging
from pathlib import Path

LOGGER = logging.getLogger(__name__)


class VisualizationExporter:
    """Export docking results for visualization (PyMOL, etc.)."""

    def __init__(self, receptor_clean: Path, receptor_pdbqt: Path) -> None:
        self.receptor_clean = receptor_clean
        self.receptor_pdbqt = receptor_pdbqt

    def generate_pymol_script(
        self,
        top_poses: list[dict],
        output_path: Path | None = None,
        include_interactions: bool = True,
    ) -> str:
        """Generate PyMOL script for visualizing top docking poses.

        Args:
            top_poses: List of top pose dicts with pose_file, affinity, etc.
            output_path: Optional path to save the script
            include_interactions: Include H-bond distance display

        Returns:
            PyMOL script content as string
        """
        pml_lines = [
            "# PyMOL script — Top docking poses",
            "# Run with:  pymol session_top_poses.pml",
            "# Or: File > Run Script",
            "",
            f"load {str(self.receptor_clean)}, receptor",
            "hide everything, receptor",
            "show cartoon, receptor",
            "color grey80, receptor",
            "spectrum count, rainbow, receptor",
            "",
            "# Load poses",
        ]

        colors = ["cyan", "magenta", "yellow", "orange", "lime", "purple", "green"]

        for idx, pose in enumerate(top_poses[:10]):  # Top 10
            if not pose.get("pose_file"):
                continue

            color = colors[idx % len(colors)]
            obj_name = f"pose_{idx}"
            affinity = pose.get("affinity", 0)
            pic50 = pose.get("predicted_pic50", "?")

            pml_lines += [
                f"load {pose['pose_file']}, {obj_name}",
                f"show sticks, {obj_name}",
                f"color {color}, {obj_name}",
                f"# {obj_name}: Affinity={affinity:.2f} kcal/mol, pIC50={pic50}",
            ]

        if include_interactions:
            pml_lines += [
                "",
                "# Show H-bonds and interactions",
                "distance hbonds, receptor, all, 3.5, mode=2",
                "color red, hbonds",
                "hide labels, hbonds",
            ]

        pml_lines += [
            "",
            "# Visualization settings",
            "bg_color white",
            "set sphere_scale, 0.3",
            "set cartoon_fancy_helices, 1",
            "zoom receptor, 20",
            "",
            '# Render high-res image',
            'print "PyMOL session loaded. Poses: ' + ", ".join(
                [f"pose_{i}" for i in range(min(10, len(top_poses)))]
            ) + '"',
        ]

        script = "\n".join(pml_lines)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(script)
            LOGGER.info(f"Saved PyMOL script: {output_path}")

        return script

    def generate_html_summary(
        self,
        interactions: list[dict],
        consensus_ranks: list[dict] | None = None,
        output_path: Path | None = None,
    ) -> str:
        """Generate interactive HTML summary of docking results.

        Args:
            interactions: List of interaction analysis dicts
            consensus_ranks: Optional consensus ranking dicts
            output_path: Optional path to save HTML

        Returns:
            HTML content as string
        """
        html_parts = [
            '<!DOCTYPE html>',
            '<html lang="en">',
            '<head>',
            '  <meta charset="UTF-8">',
            '  <meta name="viewport" content="width=device-width, initial-scale=1.0">',
            '  <title>Docking Results Summary</title>',
            '  <style>',
            "    body { font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }",
            "    h1 { color: #333; }",
            "    .section { background: white; padding: 15px; margin: 10px 0; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }",
            "    table { width: 100%; border-collapse: collapse; margin: 10px 0; }",
            "    th { background: #007bff; color: white; padding: 10px; text-align: left; }",
            "    td { padding: 10px; border-bottom: 1px solid #ddd; }",
            "    tr:hover { background: #f9f9f9; }",
            "    .interaction-item { background: #f0f8ff; padding: 10px; margin: 5px 0; border-left: 4px solid #007bff; border-radius: 3px; }",
            "    .hbond { color: #d9534f; font-weight: bold; }",
            "    .contact { color: #5cb85c; }",
            "  </style>",
            "</head>",
            "<body>",
            "  <h1>Docking Results Summary</h1>",
        ]

        if consensus_ranks:
            html_parts += [
                '  <div class="section">',
                "    <h2>Consensus Ranking</h2>",
                "    <table>",
                "      <tr><th>Rank</th><th>Ligand</th><th>SMILES</th><th>pIC50</th><th>Affinity</th><th>Score</th></tr>",
            ]
            for rank in consensus_ranks[:10]:
                html_parts.append(
                    f"      <tr>"
                    f"<td>{rank['rank']}</td>"
                    f"<td>{rank['ligand_id']}</td>"
                    f"<td><code>{rank['smiles'][:40]}...</code></td>"
                    f"<td>{rank['predicted_pic50']:.2f if rank['predicted_pic50'] else '—'}</td>"
                    f"<td>{rank['docking_affinity']:.2f if rank['docking_affinity'] else '—'}</td>"
                    f"<td>{rank['consensus_score']:.3f}</td>"
                    f"</tr>"
                )
            html_parts += ["    </table>", "  </div>"]

        if interactions:
            html_parts += [
                '  <div class="section">',
                "    <h2>Interaction Analysis (Top 10)</h2>",
            ]
            for inter in interactions[:10]:
                html_parts += [
                    f'    <div class="interaction-item">',
                    f'      <strong>{inter["ligand_id"]}</strong> - Affinity: {inter["affinity"]:.2f} kcal/mol',
                    f'      <br><span class="hbond">H-Bonds: {inter["n_hbonds"]}</span> | <span class="contact">Contacts: {inter["n_contacts"]}</span>',
                    f'      <br>Key Residues: {", ".join(inter.get("key_residues", [])[:5])}',
                    "    </div>",
                ]
            html_parts += ["  </div>"]

        html_parts += [
            "</body>",
            "</html>",
        ]

        html = "\n".join(html_parts)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(html)
            LOGGER.info(f"Saved HTML summary: {output_path}")

        return html

    def generate_json_export(
        self,
        docking_results: list[dict],
        interactions: list[dict] | None = None,
        consensus_ranks: list[dict] | None = None,
        output_path: Path | None = None,
    ) -> str:
        """Generate JSON export of all docking and analysis data.

        Args:
            docking_results: Raw docking results
            interactions: Interaction analysis
            consensus_ranks: Consensus ranking
            output_path: Optional path to save JSON

        Returns:
            JSON content as string
        """
        export_data = {
            "docking_results": docking_results,
            "interactions": interactions or [],
            "consensus_ranks": consensus_ranks or [],
            "metadata": {
                "receptor_pdbqt": str(self.receptor_pdbqt),
                "format_version": "1.0",
            },
        }

        json_str = json.dumps(export_data, indent=2)

        if output_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(json_str)
            LOGGER.info(f"Saved JSON export: {output_path}")

        return json_str
