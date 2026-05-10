'use client';

import { useState, useEffect } from 'react';
import { useScreeningContext } from '@/lib/context/ScreeningContext';
import { useDockingContext } from '@/lib/context/DockingContext';
import { useAuth } from '@/lib/context/AuthContext';
import { useRouter } from 'next/navigation';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, ScatterChart, Scatter, LineChart, Line, BoxPlot } from 'recharts';
import { Download, Search } from 'lucide-react';
import { MolecularViewer3D } from '@/components/analysis/MolecularViewer3D';

export default function AnalysisPage() {
  const router = useRouter();
  const { session: screeningSession } = useScreeningContext();
  const { job: dockingJob } = useDockingContext();
  const { token } = useAuth();
  const [activeTab, setActiveTab] = useState<'rankings' | '3d' | 'comparison' | 'history'>('rankings');
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [selectedCompoundId, setSelectedCompoundId] = useState<string | null>(null);

  const downloadCSV = () => {
    // Only export compounds that were actually submitted for docking
    const dockedResults = combinedResults.filter(r => r.bindingAffinity !== undefined || r.poseCount > 0);
    
    if (!dockedResults.length) return;
    
    const headers = ['Rank', 'CompoundId', 'SMILES', 'Consensus Score', 'Docking Affinity (kcal/mol)', 'Pose Count'];
    const rows = dockedResults.map((r, i) => [
      i + 1,
      `"${r.compoundId}"`,
      `"${r.smiles}"`,
      r.predicted_pic50?.toFixed(4) || 'N/A',
      r.bindingAffinity?.toFixed(2) || 'N/A',
      r.poseCount || 0
    ]);
    
    let csvContent = headers.join(',') + '\n' + rows.map(r => r.join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.setAttribute('download', `drug_discovery_results_${new Date().getTime()}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  useEffect(() => {
    if (activeTab === 'history' && token) {
      const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || '/api/backend';
      fetch(`${API_BASE_URL}/api/analytics/dashboard`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
        .then(res => res.json())
        .then(data => setHistoryData(data.recent_runs || []))
        .catch(console.error);
    }
  }, [activeTab, token]);

  if (!screeningSession || !dockingJob) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto space-y-8 rounded-lg border border-border bg-card p-8 text-center">
          <h2 className="text-2xl font-bold">No Active Session</h2>
          <p className="text-muted-foreground">Start a screening run first, or view your past history.</p>
          <div className="flex justify-center gap-4 mt-4">
            <button onClick={() => router.push('/screening')} className="rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground">Start Screening</button>
            <button onClick={() => setActiveTab('history')} className="rounded-lg border border-border bg-card px-6 py-3 font-semibold">View History</button>
          </div>
        </div>

        {activeTab === 'history' && (
          <div className="max-w-4xl mx-auto mt-8 rounded-lg border border-border bg-card p-6">
            <h3 className="text-lg font-semibold mb-4">Run History</h3>
            <table className="w-full text-sm">
              <thead><tr className="border-b border-border"><th className="text-left pb-2">Date</th><th className="text-left pb-2">Ensemble</th><th className="text-right pb-2">Compounds</th></tr></thead>
              <tbody>
                {historyData.map(run => (
                  <tr key={run.id} className="border-b border-border/50"><td className="py-2">{new Date(run.created_at).toLocaleDateString()}</td><td className="py-2 capitalize">{run.ensemble}</td><td className="text-right py-2">{run.compounds}</td></tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    );
  }

  const combinedResults = screeningSession.results.map((screening, idx) => {
    const docking = dockingJob.results.find(d => 
      d.smiles.trim().toLowerCase() === screening.smiles.trim().toLowerCase() ||
      (screening.canonical_smiles && d.smiles.trim().toLowerCase() === screening.canonical_smiles.trim().toLowerCase())
    );
    return { 
      ...screening, 
      compoundId: docking?.compoundId || (screening as any).compound_id || screening.compoundId || `ligand_${idx}`,
      bindingAffinity: docking?.affinity,
      poseCount: docking?.poseCount || 0,
      interactions: docking?.interactions
    };
  }).sort((a, b) => (a.bindingAffinity ?? 0) - (b.bindingAffinity ?? 0));

  const chartData = combinedResults.slice(0, 10).map((r, idx) => ({ name: r.compoundId || `Compound ${idx + 1}`, consensus: r.predicted_pic50, affinity: r.bindingAffinity || 0 }));
  const scatterData = combinedResults.map((r, idx) => ({ x: r.predicted_pic50, y: r.bindingAffinity || 0, name: r.compoundId || `Compound ${idx + 1}` }));

  useEffect(() => {
    if (combinedResults.length > 0 && !selectedCompoundId) {
      setSelectedCompoundId(combinedResults[0].compoundId);
    }
  }, [combinedResults, selectedCompoundId]);

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-6xl mx-auto space-y-8">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <h1 className="text-4xl font-bold text-foreground">Results & Analysis</h1>
          <button 
            onClick={downloadCSV}
            className="flex items-center justify-center gap-2 rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground shadow-lg hover:scale-105 transition-all"
          >
            <Download className="h-5 w-5" />
            Export Results (.CSV)
          </button>
        </div>

        <div className="grid gap-4 sm:grid-cols-4">
          <div className="rounded-lg border border-border bg-card p-4"><p className="text-sm text-muted-foreground">Total Compounds</p><p className="text-2xl font-bold text-primary">{combinedResults.length}</p></div>
          <div className="rounded-lg border border-border bg-card p-4"><p className="text-sm text-muted-foreground">Avg Affinity</p><p className="text-2xl font-bold text-primary">{(combinedResults.reduce((s, r) => s + (r.bindingAffinity || 0), 0) / combinedResults.length).toFixed(2)}</p></div>
          <div className="rounded-lg border border-border bg-card p-4"><p className="text-sm text-muted-foreground">Best Hit</p><p className="text-2xl font-bold text-primary">{combinedResults[0]?.bindingAffinity?.toFixed(2) || 'N/A'}</p></div>
        </div>

        <div className="rounded-lg border border-border bg-card overflow-hidden">
          <div className="flex gap-0 border-b border-border overflow-x-auto">
            {['rankings', '3d', 'comparison', 'history'].map(id => (
              <button key={id} onClick={() => setActiveTab(id as any)} className={`px-4 py-3 text-sm font-medium transition-colors ${activeTab === id ? 'border-b-2 border-primary text-primary' : 'text-muted-foreground hover:text-foreground'}`}>
                {id.charAt(0).toUpperCase() + id.slice(1)}
              </button>
            ))}
          </div>

          <div className="p-6">
            {activeTab === '3d' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="text-lg font-semibold">3D Binding Visualization</h3>
                  <select
                    className="bg-muted border border-border rounded-md px-3 py-1.5 text-sm outline-none focus:ring-2 focus:ring-primary"
                    value={selectedCompoundId || ''}
                    onChange={(e) => setSelectedCompoundId(e.target.value)}
                  >
                    {combinedResults.slice(0, 10).map((r, i) => (
                      <option key={i} value={r.compoundId}>{r.compoundId} (Rank {i + 1})</option>
                    ))}
                  </select>
                </div>
                {/* Dynamically import or render the MolecularViewer3D */}
                <MolecularViewer3D 
                  compoundId={selectedCompoundId || combinedResults[0]?.compoundId || 'unknown'} 
                  poseCount={combinedResults.find(r => r.compoundId === selectedCompoundId)?.poseCount || combinedResults[0]?.poseCount || 0}
                />
              </div>
            )}

            {activeTab === 'rankings' && (
              <div className="space-y-4">
                <div className="flex items-center justify-between px-4 py-2 bg-muted/50 rounded-lg">
                  <span className="text-sm text-muted-foreground font-medium">Top 5 Discovery Candidates (Consensus Ranked)</span>
                </div>
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border text-muted-foreground uppercase tracking-wider text-[10px] font-bold">
                      <th className="px-4 py-3 text-left">Rank</th>
                      <th className="px-4 py-3 text-left">Compound Identifier</th>
                      <th className="px-4 py-3 text-right">pIC50 (AI)</th>
                      <th className="px-4 py-3 text-right">Affinity (Physics)</th>
                    </tr>
                  </thead>
                  <tbody>
                    {combinedResults.slice(0, 5).map((r, idx) => (
                      <tr key={idx} className="border-b border-border hover:bg-muted/30 transition-colors">
                        <td className="px-4 py-3 font-bold text-primary">{idx + 1}</td>
                        <td className="px-4 py-3 font-mono text-xs">{r.compoundId}</td>
                        <td className="px-4 py-3 text-right font-medium">{r.predicted_pic50?.toFixed(3)}</td>
                        <td className="px-4 py-3 text-right text-primary font-bold">{r.bindingAffinity?.toFixed(2)} kcal/mol</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}



            {activeTab === 'comparison' && (
              <div className="space-y-6">
                <div className="bg-muted/30 p-4 rounded-lg border border-border">
                  <h4 className="text-sm font-semibold mb-1">AI vs Physics Correlation</h4>
                  <p className="text-xs text-muted-foreground">Identifying candidates where Deep Learning predictions (pIC50) strongly correlate with Physics-based docking energy.</p>
                </div>
                <ResponsiveContainer width="100%" height={350}>
                  <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--color-border)" />
                    <XAxis dataKey="x" name="AI Predicted pIC50" type="number" stroke="var(--color-muted-foreground)" label={{ value: 'Predicted pIC50', position: 'bottom', offset: 0 }} />
                    <YAxis dataKey="y" name="Docking Affinity" type="number" stroke="var(--color-muted-foreground)" label={{ value: 'Affinity (kcal/mol)', angle: -90, position: 'left' }} />
                    <Tooltip cursor={{ strokeDasharray: '3 3' }} contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)' }} />
                    <Scatter name="Compounds" data={scatterData} fill="var(--color-primary)" opacity={0.6} />
                  </ScatterChart>
                </ResponsiveContainer>
              </div>
            )}

            {activeTab === 'history' && (
              <div className="space-y-6">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-lg font-semibold">Discovery Timeline</h3>
                    <p className="text-xs text-muted-foreground">Historical tracking of model ensemble performance across all screening sessions.</p>
                  </div>
                </div>
                <ResponsiveContainer width="100%" height={250}>
                  <LineChart data={historyData}>
                    <CartesianGrid strokeDasharray="3 3" />
                    <XAxis dataKey="created_at" tickFormatter={(v) => new Date(v).toLocaleDateString()} stroke="var(--color-muted-foreground)" />
                    <YAxis stroke="var(--color-muted-foreground)" />
                    <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', borderColor: 'var(--color-border)' }} />
                    <Line type="monotone" dataKey="avg_pic50" stroke="var(--color-primary)" name="Avg pIC50" strokeWidth={2} dot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
                <table className="w-full text-xs mt-8">
                  <thead><tr className="border-b border-border text-muted-foreground font-bold uppercase tracking-widest text-[9px]"><th className="text-left pb-3">Session Date</th><th className="text-left pb-3">Ensemble Mode</th><th className="text-right pb-3">Batch Size</th><th className="text-right pb-3">Avg pIC50</th></tr></thead>
                  <tbody>
                    {historyData.map(run => (
                      <tr key={run.id} className="border-b border-border/50 hover:bg-muted/20 transition-colors"><td className="py-3 font-medium">{new Date(run.created_at).toLocaleString()}</td><td className="py-3 capitalize"><span className="px-2 py-0.5 bg-primary/10 text-primary rounded-full text-[10px]">{run.ensemble}</span></td><td className="text-right py-3">{run.compounds}</td><td className="text-right py-3 font-bold">{run.avg_pic50?.toFixed(2)}</td></tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
