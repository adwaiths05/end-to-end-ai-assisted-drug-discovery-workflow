'use client';

import { useEffect, useRef, useState } from 'react';
import Script from 'next/script';
import { Loader2, Search } from 'lucide-react';

interface MolecularViewerProps {
  compoundId: string;
  poseCount?: number;
}

export function MolecularViewer3D({ compoundId, poseCount = 10 }: MolecularViewerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [loaded, setLoaded] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (typeof window !== 'undefined' && (window as any).$3Dmol) {
      setLoaded(true);
    }
  }, []);

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
        // Use the relative proxy path to avoid CORS issues
        const API_BASE_URL = '/api/backend';
        
        console.log(`[3DViewer] Fetching molecules from ${API_BASE_URL} for ${compoundId}...`);
        const receptorRes = await fetch(`${API_BASE_URL}/data/docking/1IEP_clean.pdb`);
        if (!receptorRes.ok) throw new Error('Could not fetch receptor file');
        const receptorData = await receptorRes.text();
        viewer.addModel(receptorData, 'pdb');

        // Load Ligand Poses as animation frames
        const ligandRes = await fetch(`${API_BASE_URL}/data/docking/${compoundId}_out.pdbqt`);
        if (!ligandRes.ok) throw new Error(`Could not fetch docking results for ${compoundId}`);
        const ligandData = await ligandRes.text();

        // This natively parses the MODEL/ENDMDL blocks into animation frames
        viewer.addModelsAsFrames(ligandData, 'pdbqt');

        // Apply Global styles first (for all ligand poses)
        viewer.setStyle({}, { stick: { color: '#22c55e', radius: 0.25 } });
        viewer.addStyle({ atom: 'H' }, { sphere: { radius: 0 } }); // Hide ALL hydrogens

        // Override style for Model 0 (The Receptor)
        viewer.setStyle({ model: 0 }, { cartoon: { color: 'spectrum' } });

        console.log(`[3DViewer] Successfully loaded all models for ${compoundId}. Rendering...`);
        viewer.zoomTo({ model: 1 });
        viewer.render();
        viewer.resize();

        viewer.animate({ loop: "forward", interval: 1500 });

        const handleResize = () => viewer.resize();
        window.addEventListener('resize', handleResize);
        (viewer as any)._resizeHandler = handleResize;

      } catch (err: any) {
        console.error("[3DViewer] Load Error:", err);
        setError(err.message);
      }
    }

    loadMolecules();

    return () => {
      if ((viewer as any)._resizeHandler) {
        window.removeEventListener('resize', (viewer as any)._resizeHandler);
      }
      viewer.clear();
    };
  }, [loaded, compoundId]);

  return (
    <div className="relative w-full h-[600px] rounded-xl overflow-hidden border border-border bg-[#0a0a0a]">
      <Script
        src="https://3Dmol.org/build/3Dmol-min.js"
        strategy="afterInteractive"
        onLoad={() => {
          console.log("[3DViewer] 3Dmol.js script loaded.");
          setLoaded(true);
        }}
      />
      {error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-background/90 z-20 backdrop-blur-md p-6 text-center">
          <div className="bg-destructive/10 p-4 rounded-full mb-4">
            <Search className="h-8 w-8 text-destructive" />
          </div>
          <p className="text-destructive font-bold mb-2">Visualization Error</p>
          <p className="text-muted-foreground text-sm max-w-md mb-6">{error}</p>
          <div className="flex gap-3">
             <a 
               href={`/api/backend/data/docking/${compoundId}_out.pdbqt`} 
               target="_blank" 
               className="text-xs text-primary underline hover:text-primary/80"
             >
               Try Direct Download
             </a>
          </div>
        </div>
      )}
      {!loaded && !error && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-[#0a0a0a] z-10">
          <Loader2 className="h-8 w-8 text-primary animate-spin mb-4" />
          <p className="text-muted-foreground animate-pulse font-medium">Mounting 3D Engine...</p>
        </div>
      )}
      <div ref={containerRef} className="absolute inset-0 w-full h-full" />

      {/* Overlay UI */}
      <div className="absolute bottom-4 left-4 right-4 flex justify-between items-end pointer-events-none z-30">
        <div className="bg-background/80 backdrop-blur-md px-4 py-3 rounded-lg border border-border pointer-events-auto shadow-2xl">
          <div className="flex items-center gap-2 mb-1">
            <div className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            <h4 className="font-bold text-primary tracking-tight">{compoundId}</h4>
          </div>
          <p className="text-[10px] uppercase tracking-widest text-muted-foreground font-semibold">Active Simulation • {poseCount} Poses</p>
        </div>
        <div className="bg-background/80 backdrop-blur-sm px-3 py-2 rounded-lg border border-border text-xs text-muted-foreground">
          Left Click: Rotate • Right Click: Translate • Scroll: Zoom
        </div>
      </div>
    </div>
  );
}
