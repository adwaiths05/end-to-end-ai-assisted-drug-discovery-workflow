'use client';

import { DockingResult } from '@/lib/context/DockingContext';
import { ChevronDown } from 'lucide-react';
import React, { useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, ZAxis, LineChart, Line } from 'recharts';

interface DockingResultsProps {
  results: DockingResult[];
}

export function DockingResults({ results }: DockingResultsProps) {
  const [selectedLigandIndex, setSelectedLigandIndex] = useState(0);
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);

  if (results.length === 0) {
    return <div className="rounded-lg border border-border bg-card p-8 text-center"><p className="text-muted-foreground">No results yet. Results will appear after docking completes.</p></div>;
  }

  const sorted = [...results].sort((a, b) => (a.affinity ?? 1) - (b.affinity ?? -1));
  const successCount = sorted.filter(r => r.status === 'success' && r.affinity != null).length;
  
  // Chart 1: Affinity Bar Chart (Top 10)
  const barData = sorted.slice(0, 10).map((r, i) => ({
    name: r.compoundId || `Rank ${i+1}`,
    affinity: r.affinity || 0
  }));

  // Chart 2: Pose Energy Line Chart (Selected Ligand)
  const selectedLigand = sorted[selectedLigandIndex];
  const poseData = selectedLigand?.details?.energies?.map((energy: number, index: number) => ({
    pose: `Pose ${index + 1}`,
    affinity: energy
  })) || [];

  return (
    <div className="space-y-8">
      {/* 3 New Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        {/* Chart 1: Affinity Bar */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-sm font-semibold text-foreground">Top 10 Binding Affinities (kcal/mol)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={barData} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--color-border)" />
              <XAxis type="number" stroke="var(--color-muted-foreground)" domain={['auto', 'auto']} />
              <YAxis dataKey="name" type="category" width={80} stroke="var(--color-muted-foreground)" tick={{fontSize: 11}} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)' }} />
              <Bar dataKey="affinity" fill="var(--color-chart-1)" radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 2: Pose Energy Line (Dynamic Selection) */}
        <div className="rounded-lg border border-border bg-card p-6">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-foreground">Pose Energies ({selectedLigand?.compoundId || 'Selected'})</h3>
            <select 
              className="bg-muted border border-border rounded px-2 py-1 text-xs outline-none focus:ring-1 focus:ring-primary"
              value={selectedLigandIndex}
              onChange={(e) => setSelectedLigandIndex(parseInt(e.target.value))}
            >
              {sorted.slice(0, 10).map((r, i) => (
                <option key={i} value={i}>{r.compoundId || `Rank ${i+1}`}</option>
              ))}
            </select>
          </div>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={poseData}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="pose" stroke="var(--color-muted-foreground)" tick={{fontSize: 11}} />
              <YAxis stroke="var(--color-muted-foreground)" domain={['auto', 'auto']} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)' }} />
              <Line type="monotone" dataKey="affinity" stroke="var(--color-primary)" strokeWidth={2} dot={{r: 4}} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      </div>

      <div className="space-y-4 rounded-lg border border-border bg-card p-6">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Docking Results</h3>
          <span className="rounded-full bg-primary/10 px-3 py-1 text-primary text-xs font-semibold">{successCount} docked</span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left font-semibold text-foreground">Rank</th>
                <th className="px-4 py-3 text-left font-semibold text-foreground">Compound</th>
                <th className="px-4 py-3 text-right font-semibold text-foreground">Affinity</th>
                <th className="px-4 py-3 text-center font-semibold text-foreground">Poses</th>
                <th className="px-4 py-3 text-center font-semibold text-foreground">Status</th>
                <th className="px-4 py-3 text-center font-semibold text-foreground"></th>
              </tr>
            </thead>
            <tbody>
              {sorted.map((result, idx) => (
                <React.Fragment key={idx}>
                  <tr className="border-b border-border hover:bg-muted/50 cursor-pointer" onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}>
                    <td className="px-4 py-3 font-medium">{result.status === 'success' ? idx + 1 : '—'}</td>
                    <td className="px-4 py-3 text-xs font-mono">{result.compoundId}</td>
                    <td className="px-4 py-3 text-right">
                      {result.affinity != null ? <span className="rounded-full bg-primary/10 px-2 py-1 text-primary font-semibold">{result.affinity.toFixed(2)}</span> : '—'}
                    </td>
                    <td className="px-4 py-3 text-center text-muted-foreground">{result.poseCount}</td>
                    <td className="px-4 py-3 text-center text-green-500 font-semibold">{result.status}</td>
                    <td className="px-4 py-3 text-center"><ChevronDown className={`h-4 w-4 mx-auto text-primary transition-transform ${expandedIndex === idx ? 'rotate-180' : ''}`} /></td>
                  </tr>
                  {expandedIndex === idx && (
                    <tr key={`${idx}-expanded`}>
                      <td colSpan={6} className="px-4 py-4 bg-muted/20">
                        <pre className="text-xs text-muted-foreground overflow-auto max-h-32">{JSON.stringify(result.details, null, 2)}</pre>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
