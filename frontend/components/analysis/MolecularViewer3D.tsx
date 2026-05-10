'use client';

import { useEffect, useRef, useState } from 'react';
import Script from 'next/script';

interface MolecularViewerProps {
  compoundId: string;
  fileName: string;
}

export function MolecularViewer3D({ compoundId, fileName }: MolecularViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!loaded || !containerRef.current) return;
    if (typeof window === 'undefined' || !(window as any).$3Dmol) return;

    const $3Dmol = (window as any).$3Dmol;
    const viewer = $3Dmol.createViewer(containerRef.current, {
      backgroundColor: '#121212',
    });

    async function loadMolecules() {
      try {
        setError(null);
        // Load Receptor
        const receptorRes = await fetch('http://localhost:8000/data/docking/1IEP_receptor.pdbqt');
        if (!receptorRes.ok) throw new Error('Could not fetch receptor file');
        const receptorData = await receptorRes.text();
        viewer.addModel(receptorData, 'pdbqt');

        // Load Ligand Poses as animation frames
        const ligandRes = await fetch(`http://localhost:8000/data/docking/${fileName}`);
        if (!ligandRes.ok) throw new Error(`Could not fetch docking results for ${compoundId}`);
        const ligandData = await ligandRes.text();

        // This natively parses the MODEL/ENDMDL blocks into animation frames
        viewer.addModelsAsFrames(ligandData, 'pdbqt');

        // Style 1: Base Receptor as colorful ribbon
        viewer.setStyle({ model: 0 }, { cartoon: { color: 'spectrum' } });

        // Style 2: Ligand poses as thick green sticks
        // Model 1 refers to the ligand frames
        viewer.setStyle({ model: 1 }, { stick: { color: '#22c55e', radius: 0.25 } });

        // Style 3: Interacting Residues (protein amino acids within 5A of the drug)
        // Render them as white/gray sticks
        viewer.addStyle(
          { model: 0, within: { distance: 5.0, sel: { model: 1 } } },
          { stick: { colorscheme: 'whiteCarbon', radius: 0.15 } }
        );

        // Style 4: Cavity Surface
        // Generate a semi-transparent gray surface mesh around the binding pocket
        viewer.addSurface($3Dmol.SurfaceType.VDW, {
          opacity: 0.3,
          color: '#808080'
        }, { model: 0, within: { distance: 5.0, sel: { model: 1 } } }, { sel: { model: 1 } });

        // Auto-Zoom straight into the drug
        viewer.zoomTo({ model: 1 });
        viewer.render();

        // Auto-Animate through the 10 poses
        viewer.animate({ loop: "forward", interval: 1500 });
      } catch (err: any) {
        console.error("Error loading molecules", err);
        setError(err.message);
      }
    }

    loadMolecules();

    return () => {
      viewer.clear();
    };
  }, [loaded, compoundId]);

  return (
    <div className="relative w-full h-[600px] rounded-xl overflow-hidden border border-border bg-[#121212]">
      <Script
        src="https://3Dmol.org/build/3Dmol-min.js"
        onLoad={() => setLoaded(true)}
      />
      {error && (
        <div className="absolute inset-0 flex items-center justify-center bg-background/80 z-10 backdrop-blur-sm">
          <p className="text-destructive font-medium bg-destructive/10 px-4 py-2 rounded-lg border border-destructive/20">{error}</p>
        </div>
      )}
      {!loaded && !error && (
        <div className="absolute inset-0 flex items-center justify-center">
          <p className="text-muted-foreground animate-pulse">Loading 3Dmol.js Viewer...</p>
        </div>
      )}
      <div ref={containerRef} className="absolute inset-0" />

      {/* Overlay UI */}
      <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end pointer-events-none">
        <div className="bg-background/80 backdrop-blur-sm px-4 py-3 rounded-lg border border-border pointer-events-auto">
          <h4 className="font-semibold text-primary">{compoundId}</h4>
          <p className="text-xs text-muted-foreground mt-1">Animating 10 Binding Poses</p>
        </div>
        <div className="bg-background/80 backdrop-blur-sm px-3 py-2 rounded-lg border border-border text-xs text-muted-foreground">
          Left Click: Rotate • Right Click: Translate • Scroll: Zoom
        </div>
      </div>
    </div>
  );
}
