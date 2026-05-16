'use client';

import { useScreeningContext } from '@/lib/context/ScreeningContext';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  ScatterChart, Scatter, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, Radar, Cell,
  ZAxis
} from 'recharts';
import { Download, Save, ThumbsUp, ThumbsDown, Search } from 'lucide-react';
import { downloadScreeningCSV, downloadScreeningJSON } from '@/lib/utils/export';
import React, { useState } from 'react';
import { useAuth } from '@/lib/context/AuthContext';

interface ScreeningResultsProps {
  onProceedToDocking: () => void;
}

const MODEL_LABELS: Record<string, string> = { rf: 'Random Forest', xgb: 'XGBoost', mpnn: 'MPNN', gin: 'GIN' };
const MODEL_COLORS = ['var(--color-chart-1)', 'var(--color-chart-2)', 'var(--color-chart-3)', 'var(--color-chart-4)'];

export function ScreeningResults({ onProceedToDocking }: ScreeningResultsProps) {
  const { session } = useScreeningContext();
  const { token } = useAuth();
  const [expandedIndex, setExpandedIndex] = useState<number | null>(null);
  const [feedbackState, setFeedbackState] = useState<Record<string, string>>({});

  if (!session || session.results.length === 0) return null;

  const { results, activeEnsemble, count } = session;
  const validResults = results.filter(r => r.valid && r.predicted_pic50 != null).sort((a, b) => (b.predicted_pic50 ?? 0) - (a.predicted_pic50 ?? 0));
  const topHits = validResults.slice(0, 10);
  
  // Data for pIC50 Histogram
  const histogramBins = Array.from({ length: 10 }, (_, i) => ({ name: `Bin ${i}`, count: 0, range: '' }));
  if (validResults.length > 0) {
    const min = Math.min(...validResults.map(r => r.predicted_pic50 ?? 0));
    const max = Math.max(...validResults.map(r => r.predicted_pic50 ?? 0));
    const step = max === min ? 1 : (max - min) / 10;
    
    validResults.forEach(r => {
      let idx = Math.floor(((r.predicted_pic50 ?? 0) - min) / step);
      if (isNaN(idx) || !isFinite(idx)) idx = 0;
      idx = Math.max(0, Math.min(9, idx));
      
      histogramBins[idx].count++;
      histogramBins[idx].range = `${(min + idx * step).toFixed(1)}-${(min + (idx + 1) * step).toFixed(1)}`;
    });
  }

  // Data for Confidence Scatter
  const scatterData = validResults.map(r => ({
    x: r.predicted_pic50,
    y: r.confidence,
    z: r.uncertainty,
    name: r.compoundId || 'Unknown'
  }));

  // Data for Radar (Top 1)
  const topHit = topHits[0];
  const radarData = topHit ? Object.keys(MODEL_LABELS).map(key => ({
    subject: MODEL_LABELS[key],
    A: topHit.model_predictions[key] || 0,
    fullMark: 10
  })) : [];

  const handleFeedback = (compoundId: string, label: string) => {
    setFeedbackState(prev => ({ ...prev, [compoundId]: label }));
    // In a real app, make an API call to POST /feedback
  };

  return (
    <div className="space-y-8">
      {/* 4 New Charts Section */}
      <div className="grid gap-6 lg:grid-cols-2">
        
        {/* Chart 1: pIC50 Histogram */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-sm font-semibold text-foreground">pIC50 Distribution (Batch)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={histogramBins.filter(b => b.count > 0)}>
              <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
              <XAxis dataKey="range" stroke="var(--color-muted-foreground)" tick={{fontSize: 10}} />
              <YAxis stroke="var(--color-muted-foreground)" />
              <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)' }} />
              <Bar dataKey="count" fill="var(--color-primary)" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 2: Confidence vs pIC50 Scatter */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-sm font-semibold text-foreground">Confidence vs pIC50 (Size = Uncertainty)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <ScatterChart>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
              <XAxis dataKey="x" type="number" name="pIC50" stroke="var(--color-muted-foreground)" />
              <YAxis dataKey="y" type="number" name="Confidence" stroke="var(--color-muted-foreground)" />
              <ZAxis dataKey="z" range={[20, 100]} name="Uncertainty" />
              <Tooltip cursor={{strokeDasharray: '3 3'}} contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)', color: 'white' }} itemStyle={{ color: 'white' }} labelStyle={{ color: 'white' }} />
              <Scatter name="Compounds" data={scatterData} fill="var(--color-chart-2)" opacity={0.6} />
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 3: Model Radar (Top Hit) */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-sm font-semibold text-foreground">Top Hit Model Agreement ({topHit?.compoundId || 'Rank 1'})</h3>
          <ResponsiveContainer width="100%" height={250}>
            <RadarChart cx="50%" cy="50%" outerRadius="80%" data={radarData}>
              <PolarGrid stroke="var(--color-border)" />
              <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--color-muted-foreground)', fontSize: 11 }} />
              <PolarRadiusAxis angle={30} domain={[0, 10]} />
              <Radar name="pIC50" dataKey="A" stroke="var(--color-primary)" fill="var(--color-primary)" fillOpacity={0.5} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)' }} />
            </RadarChart>
          </ResponsiveContainer>
        </div>

        {/* Chart 4: Lipinski Compliance */}
        <div className="rounded-lg border border-border bg-card p-6">
          <h3 className="mb-4 text-sm font-semibold text-foreground">Lipinski Profile (Top Hit)</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={[
              { name: 'MW (<500)', value: topHit?.metadata?.mw || 0, limit: 500 },
              { name: 'LogP (<5)', value: topHit?.metadata?.logp || 0, limit: 5 },
              { name: 'HBD (<5)', value: topHit?.metadata?.hbd || 0, limit: 5 },
              { name: 'HBA (<10)', value: topHit?.metadata?.hba || 0, limit: 10 }
            ]} layout="vertical">
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="var(--color-border)" />
              <XAxis type="number" stroke="var(--color-muted-foreground)" />
              <YAxis dataKey="name" type="category" width={80} stroke="var(--color-muted-foreground)" tick={{fontSize: 11}} />
              <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)' }} />
              <Bar dataKey="value" fill="var(--color-chart-3)" radius={[0, 4, 4, 0]}>
                {/* Dynamically color based on limit violation */}
                {topHit && [topHit.metadata?.mw, topHit.metadata?.logp, topHit.metadata?.hbd, topHit.metadata?.hba].map((val, idx) => (
                  <Cell key={idx} fill={(val > [500, 5, 5, 10][idx]) ? 'var(--color-destructive)' : 'var(--color-chart-3)'} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Hits Table */}
      <div className="rounded-lg border border-border bg-card p-6">
        <h3 className="mb-4 text-lg font-semibold text-foreground">Top Hits by pIC50</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="px-4 py-3 text-left font-semibold">Rank</th>
                <th className="px-4 py-3 text-left font-semibold">ID</th>
                <th className="px-4 py-3 text-left font-semibold">SMILES</th>
                <th className="px-4 py-3 text-right font-semibold">pIC50</th>
                <th className="px-4 py-3 text-center font-semibold">Feedback</th>
                <th className="px-4 py-3 text-center font-semibold">Details</th>
              </tr>
            </thead>
            <tbody>
              {topHits.map((result, idx) => (
                <React.Fragment key={idx}>
                  <tr className="border-b border-border hover:bg-muted/50 transition-colors cursor-pointer" onClick={() => setExpandedIndex(expandedIndex === idx ? null : idx)}>
                    <td className="px-4 py-3 text-foreground font-medium">{idx === 0 ? '🥇' : idx === 1 ? '🥈' : idx === 2 ? '🥉' : idx + 1}</td>
                    <td className="px-4 py-3 text-foreground text-xs">{result.compoundId || `Compound ${idx + 1}`}</td>
                    <td className="px-4 py-3 text-muted-foreground text-xs font-mono max-w-xs truncate">{result.canonical_smiles || result.smiles}</td>
                    <td className="px-4 py-3 text-right"><span className="rounded-full bg-primary/10 px-3 py-1 text-primary font-semibold">{result.predicted_pic50?.toFixed(3)}</span></td>
                    <td className="px-4 py-3 text-center" onClick={(e) => e.stopPropagation()}>
                      <div className="flex items-center justify-center gap-2">
                        <button onClick={() => handleFeedback(result.compoundId || `${idx}`, 'promising')} className={`p-1.5 rounded hover:bg-muted ${feedbackState[result.compoundId || `${idx}`] === 'promising' ? 'text-green-500 bg-green-500/10' : 'text-muted-foreground'}`}><ThumbsUp className="h-4 w-4" /></button>
                        <button onClick={() => handleFeedback(result.compoundId || `${idx}`, 'reject')} className={`p-1.5 rounded hover:bg-muted ${feedbackState[result.compoundId || `${idx}`] === 'reject' ? 'text-destructive bg-destructive/10' : 'text-muted-foreground'}`}><ThumbsDown className="h-4 w-4" /></button>
                        <button onClick={() => handleFeedback(result.compoundId || `${idx}`, 'review')} className={`p-1.5 rounded hover:bg-muted ${feedbackState[result.compoundId || `${idx}`] === 'review' ? 'text-yellow-500 bg-yellow-500/10' : 'text-muted-foreground'}`}><Search className="h-4 w-4" /></button>
                      </div>
                    </td>
                    <td className="px-4 py-3 text-center text-primary text-xs">{expandedIndex === idx ? '▲' : '▼'}</td>
                  </tr>
                  {expandedIndex === idx && (
                    <tr key={`${idx}-expanded`}>
                      <td colSpan={6} className="px-4 py-4 bg-muted/20">
                        <div className="space-y-3">
                          <p className="text-xs font-semibold text-foreground">Per-Model Predictions (pIC50)</p>
                          <div className="flex flex-wrap gap-3">
                            {Object.keys(MODEL_LABELS).map(k => (
                              <div key={k} className="rounded border border-border bg-card px-3 py-2">
                                <p className="text-xs text-muted-foreground">{MODEL_LABELS[k]}</p>
                                <p className="text-sm font-bold text-primary">{result.model_predictions[k]?.toFixed(3) ?? '—'}</p>
                              </div>
                            ))}
                          </div>
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Export & Actions */}
      <div className="flex flex-col gap-4 sm:flex-row">
        <button onClick={() => downloadScreeningCSV(validResults)} className="flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-4 py-3 font-semibold text-foreground hover:bg-accent"><Download className="h-4 w-4" /> CSV</button>
        <button onClick={() => downloadScreeningJSON(validResults, activeEnsemble)} className="flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-4 py-3 font-semibold text-foreground hover:bg-accent"><Download className="h-4 w-4" /> JSON</button>
        <button onClick={onProceedToDocking} className="ml-auto rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground hover:scale-105 transition-all">Proceed to Docking →</button>
      </div>
    </div>
  );
}
