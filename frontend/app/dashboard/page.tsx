'use client';

import { useEffect, useState } from 'react';
import { useAuth } from '@/lib/context/AuthContext';
import { useRouter } from 'next/navigation';
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';
import { Activity, Database, Target, Trophy } from 'lucide-react';

export default function DashboardPage() {
  const { user, token, loading } = useAuth();
  const router = useRouter();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (!loading && !user) {
      router.push('/login');
    }
  }, [user, loading, router]);

  useEffect(() => {
    if (token) {
      fetch('http://localhost:8000/api/analytics/dashboard', {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      .then(res => res.json())
      .then(setData)
      .catch(console.error);
    }
  }, [token]);

  if (loading || !user || !data) {
    return <div className="flex h-screen items-center justify-center">Loading dashboard...</div>;
  }

  // Process data for charts
  const runsData = data.recent_runs.map((r: any) => ({
    date: new Date(r.created_at).toLocaleDateString(),
    compounds: r.compounds
  })).reverse();

  const ensembleCounts = data.recent_runs.reduce((acc: any, run: any) => {
    acc[run.ensemble] = (acc[run.ensemble] || 0) + 1;
    return acc;
  }, {});

  const pieData = Object.keys(ensembleCounts).map(k => ({ name: k, value: ensembleCounts[k] }));
  const COLORS = ['var(--color-chart-1)', 'var(--color-chart-2)', 'var(--color-chart-3)', 'var(--color-chart-4)'];

  return (
    <div className="container mx-auto px-4 py-8 space-y-8">
      {/* Welcome Banner */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-foreground">Welcome back, {user.name.split(' ')[0]}</h1>
          <p className="text-muted-foreground mt-1">Here is the latest activity in your workspace.</p>
        </div>
        <button
          onClick={() => router.push('/screening')}
          className="rounded-lg bg-primary px-6 py-2.5 font-semibold text-primary-foreground hover:bg-primary/90 transition-colors"
        >
          New Screening
        </button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-primary/10 p-3"><Activity className="h-6 w-6 text-primary" /></div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Total Runs</p>
              <p className="text-2xl font-bold text-foreground">{data.stats.total_runs}</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-primary/10 p-3"><Database className="h-6 w-6 text-primary" /></div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Compounds Screened</p>
              <p className="text-2xl font-bold text-foreground">{data.stats.total_compounds}</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-primary/10 p-3"><Trophy className="h-6 w-6 text-primary" /></div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Best pIC50</p>
              <p className="text-2xl font-bold text-foreground">{data.stats.best_pic50.toFixed(2)}</p>
            </div>
          </div>
        </div>
        <div className="rounded-xl border border-border bg-card p-6">
          <div className="flex items-center gap-4">
            <div className="rounded-lg bg-primary/10 p-3"><Target className="h-6 w-6 text-primary" /></div>
            <div>
              <p className="text-sm font-medium text-muted-foreground">Avg Confidence</p>
              <p className="text-2xl font-bold text-foreground">{(data.stats.avg_confidence * 100).toFixed(0)}%</p>
            </div>
          </div>
        </div>
      </div>

      <div className="grid gap-8 lg:grid-cols-3">
        {/* Activity Chart */}
        <div className="lg:col-span-2 rounded-xl border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-6">Recent Activity (Compounds Screened)</h3>
          <div className="h-[300px]">
            {runsData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={runsData}>
                  <defs>
                    <linearGradient id="colorCompounds" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="var(--color-primary)" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="var(--color-primary)" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--color-border)" />
                  <XAxis dataKey="date" stroke="var(--color-muted-foreground)" />
                  <YAxis stroke="var(--color-muted-foreground)" />
                  <Tooltip 
                    contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: '8px' }}
                  />
                  <Area type="monotone" dataKey="compounds" stroke="var(--color-primary)" strokeWidth={2} fillOpacity={1} fill="url(#colorCompounds)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">No recent activity</div>
            )}
          </div>
        </div>

        {/* Ensemble Doughnut */}
        <div className="rounded-xl border border-border bg-card p-6">
          <h3 className="text-lg font-semibold mb-6">Ensemble Usage</h3>
          <div className="h-[300px]">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip contentStyle={{ backgroundColor: 'var(--color-card)', border: '1px solid var(--color-border)', borderRadius: '8px' }} />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <div className="flex h-full items-center justify-center text-muted-foreground">No runs yet</div>
            )}
            {pieData.length > 0 && (
              <div className="flex justify-center gap-4 mt-4">
                {pieData.map((entry, index) => (
                  <div key={entry.name} className="flex items-center gap-2">
                    <span className="w-3 h-3 rounded-full" style={{ backgroundColor: COLORS[index % COLORS.length] }}></span>
                    <span className="text-sm text-muted-foreground capitalize">{entry.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Recent Runs Table */}
      <div className="rounded-xl border border-border bg-card p-6">
        <h3 className="text-lg font-semibold mb-6">Recent Screening Runs</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="pb-3 text-left font-medium text-muted-foreground">Date</th>
                <th className="pb-3 text-left font-medium text-muted-foreground">Ensemble</th>
                <th className="pb-3 text-right font-medium text-muted-foreground">Compounds</th>
                <th className="pb-3 text-right font-medium text-muted-foreground">Avg pIC50</th>
                <th className="pb-3 text-center font-medium text-muted-foreground">Status</th>
              </tr>
            </thead>
            <tbody>
              {data.recent_runs.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-8 text-center text-muted-foreground">No screening runs yet.</td>
                </tr>
              )}
              {data.recent_runs.map((run: any) => (
                <tr key={run.id} className="border-b border-border/50 hover:bg-muted/30 transition-colors">
                  <td className="py-4 text-foreground">{new Date(run.created_at).toLocaleString()}</td>
                  <td className="py-4 text-foreground capitalize">{run.ensemble}</td>
                  <td className="py-4 text-right text-foreground">{run.compounds}</td>
                  <td className="py-4 text-right text-foreground">{run.avg_pic50?.toFixed(2) || '—'}</td>
                  <td className="py-4 text-center">
                    <span className="inline-flex items-center rounded-full bg-green-500/10 px-2 py-1 text-xs font-medium text-green-500">
                      {run.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
