'use client';

import { useState } from 'react';
import { ScreeningResult, useScreeningContext } from '@/lib/context/ScreeningContext';
import { Loader2, ChevronDown } from 'lucide-react';

interface DockingConfigurationProps {
  topHits: ScreeningResult[];
  onSubmit: (selectedCompounds: ScreeningResult[], parameters: DockingParameters) => void;
  isLoading: boolean;
}

export interface DockingParameters {
  exhaustiveness: number;
  poses: number;
  cpuThreads: number;
  gridSpacing?: number;
  searchSpace?: { x: number; y: number; z: number };
  center?: { x: number; y: number; z: number };
}

export function DockingConfiguration({ topHits, onSubmit, isLoading }: DockingConfigurationProps) {
  const [selectedCompounds, setSelectedCompounds] = useState<Set<string>>(
    new Set(topHits.slice(0, 5).map((_, idx) => idx.toString()))
  );
  const [exhaustiveness, setExhaustiveness] = useState(12);
  const [poses, setPoses] = useState(10);
  const [cpuThreads, setCpuThreads] = useState(4);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [gridSpacing, setGridSpacing] = useState(0.375);
  const [searchSpaceX, setSearchSpaceX] = useState(20);
  const [searchSpaceY, setSearchSpaceY] = useState(20);
  const [searchSpaceZ, setSearchSpaceZ] = useState(20);
  const [centerX, setCenterX] = useState(15.0);
  const [centerY, setCenterY] = useState(12.0);
  const [centerZ, setCenterZ] = useState(21.0);

  const handleCompoundToggle = (index: string) => {
    setSelectedCompounds((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(index)) {
        newSet.delete(index);
      } else {
        newSet.add(index);
      }
      return newSet;
    });
  };

  const handleSubmit = () => {
    const selected = topHits.filter((_, idx) => selectedCompounds.has(idx.toString()));
    
    if (selected.length === 0) {
      alert('Please select at least one compound');
      return;
    }

    onSubmit(selected, {
      exhaustiveness,
      poses,
      cpuThreads,
      gridSpacing,
      searchSpace: { x: searchSpaceX, y: searchSpaceY, z: searchSpaceZ },
      center: { x: centerX, y: centerY, z: centerZ }
    });
  };

  return (
    <div className="space-y-6 rounded-lg border border-border bg-card p-6">
      {/* Compound Selection */}
      <div className="space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
          <div>
            <h3 className="text-lg font-semibold text-foreground">Select Compounds for Docking</h3>
            <p className="text-sm text-muted-foreground mt-1">
              {selectedCompounds.size} of {topHits.length} compounds selected
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground whitespace-nowrap">Select top:</span>
            <input
              type="number"
              min="1"
              max={topHits.length}
              defaultValue="5"
              onChange={(e) => {
                const n = Math.min(Math.max(1, parseInt(e.target.value) || 0), topHits.length);
                if (n > 0) {
                  setSelectedCompounds(new Set(topHits.slice(0, n).map((_, idx) => idx.toString())));
                }
              }}
              className="w-20 rounded border border-border bg-card px-2 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>
        </div>
        <div className="space-y-2 max-h-48 overflow-y-auto mt-4">
          {topHits.map((hit, idx) => (
            <label
              key={idx}
              className="flex items-center gap-3 rounded-lg border border-border bg-muted/50 p-3 cursor-pointer transition-colors hover:border-primary hover:bg-muted"
            >
              <input
                type="checkbox"
                checked={selectedCompounds.has(idx.toString())}
                onChange={() => handleCompoundToggle(idx.toString())}
                className="rounded border-border"
              />
              <div className="flex-1">
                <p className="font-medium text-foreground">{hit.compoundId || `Compound ${idx + 1}`}</p>
                <p className="text-xs text-muted-foreground font-mono truncate">{hit.canonical_smiles || hit.smiles}</p>
              </div>
              <span className="text-sm font-semibold text-primary">
                pIC50: {hit.predicted_pic50?.toFixed(2) ?? '—'}
              </span>
            </label>
          ))}
        </div>
      </div>

      {/* Basic Parameters */}
      <div className="space-y-4 border-t border-border pt-6">
        <h4 className="font-semibold text-foreground">Docking Parameters</h4>

        <div className="grid gap-4 sm:grid-cols-3">
          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">
              Exhaustiveness
            </label>
            <input
              type="range"
              min="1"
              max="32"
              value={exhaustiveness}
              onChange={(e) => setExhaustiveness(Number(e.target.value))}
              className="w-full"
            />
            <div className="text-center text-sm text-muted-foreground">{exhaustiveness}</div>
            <p className="text-xs text-muted-foreground">
              Higher = more thorough but slower (8-16 recommended)
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">
              Number of Poses
            </label>
            <input
              type="range"
              min="1"
              max="20"
              value={poses}
              onChange={(e) => setPoses(Number(e.target.value))}
              className="w-full"
            />
            <div className="text-center text-sm text-muted-foreground">{poses}</div>
            <p className="text-xs text-muted-foreground">
              Output poses per compound (1-20)
            </p>
          </div>

          <div className="space-y-2">
            <label className="block text-sm font-medium text-foreground">
              CPU Threads
            </label>
            <input
              type="range"
              min="1"
              max="16"
              value={cpuThreads}
              onChange={(e) => setCpuThreads(Number(e.target.value))}
              className="w-full"
            />
            <div className="text-center text-sm text-muted-foreground">{cpuThreads}</div>
            <p className="text-xs text-muted-foreground">
              Parallel processing threads
            </p>
          </div>
        </div>
      </div>

      {/* Advanced Options */}
      <div className="border-t border-border pt-6">
        <button
          onClick={() => setShowAdvanced(!showAdvanced)}
          className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
        >
          <ChevronDown
            className={`h-4 w-4 transition-transform ${showAdvanced ? 'rotate-180' : ''}`}
          />
          Advanced Options
        </button>

        {showAdvanced && (
          <div className="mt-4 space-y-4 rounded-lg border border-border bg-muted/30 p-4">
            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">
                Grid Spacing (Å)
              </label>
              <input
                type="number"
                step="0.05"
                value={gridSpacing}
                onChange={(e) => setGridSpacing(Number(e.target.value))}
                className="w-full rounded-lg border border-border bg-card px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
              />
              <p className="text-xs text-muted-foreground">
                Default: 0.375 Å (smaller = finer grid, slower)
              </p>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">
                Search Space Size
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'X', value: searchSpaceX, onChange: setSearchSpaceX },
                  { label: 'Y', value: searchSpaceY, onChange: setSearchSpaceY },
                  { label: 'Z', value: searchSpaceZ, onChange: setSearchSpaceZ },
                ].map(({ label, value, onChange }) => (
                  <div key={label}>
                    <label className="block text-xs text-muted-foreground mb-1">{label} (Å)</label>
                    <input
                      type="number"
                      value={value}
                      onChange={(e) => onChange(Number(e.target.value))}
                      className="w-full rounded-lg border border-border bg-card px-2 py-1 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                Define the cubic search box around the binding site. Increase to 80x80x80 for Blind Docking.
              </p>
            </div>

            <div className="space-y-2">
              <label className="block text-sm font-medium text-foreground">
                Grid Center Coordinates
              </label>
              <div className="grid grid-cols-3 gap-2">
                {[
                  { label: 'X', value: centerX, onChange: setCenterX },
                  { label: 'Y', value: centerY, onChange: setCenterY },
                  { label: 'Z', value: centerZ, onChange: setCenterZ },
                ].map(({ label, value, onChange }) => (
                  <div key={label}>
                    <label className="block text-xs text-muted-foreground mb-1">{label}</label>
                    <input
                      type="number"
                      step="0.5"
                      value={value}
                      onChange={(e) => onChange(Number(e.target.value))}
                      className="w-full rounded-lg border border-border bg-card px-2 py-1 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                    />
                  </div>
                ))}
              </div>
              <p className="text-xs text-muted-foreground">
                Center of the target binding pocket (Defaults to 1IEP ATP site).
              </p>
            </div>
          </div>
        )}
      </div>

      {/* Submit Button */}
      <div className="border-t border-border pt-6">
        <button
          onClick={handleSubmit}
          disabled={isLoading || selectedCompounds.size === 0}
          className="w-full rounded-lg bg-primary px-6 py-4 font-semibold text-primary-foreground transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
        >
          {isLoading && <Loader2 className="h-4 w-4 animate-spin" />}
          {isLoading ? 'Starting Docking...' : 'Start Docking'}
        </button>
      </div>
    </div>
  );
}
