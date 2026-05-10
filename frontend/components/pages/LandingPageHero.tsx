'use client';

import Link from 'next/link';
import { ArrowRight, Beaker, Database, Shield } from 'lucide-react';
import { useEffect, useState } from 'react';

export function LandingPageHero() {
  const [stats, setStats] = useState({ total_runs: 0, total_compounds: 0, avg_pic50: 0 });
  const [recent, setRecent] = useState<any[]>([]);

  useEffect(() => {
    fetch('http://localhost:8000/api/analytics/summary')
      .then(res => res.json())
      .then(data => {
        if (data.stats) setStats(data.stats);
        if (data.recent_discoveries) setRecent(data.recent_discoveries);
      })
      .catch(console.error);
  }, []);

  return (
    <section className="relative overflow-hidden bg-gradient-to-b from-primary/5 to-transparent py-20 sm:py-28">
      <div className="container mx-auto px-4">
        <div className="mx-auto max-w-3xl space-y-8 text-center">
          {/* Badge */}
          <div className="inline-block rounded-full border border-primary/30 bg-primary/10 px-4 py-2">
            <p className="text-sm font-medium text-primary">Deploy-Ready AI Drug Discovery</p>
          </div>

          {/* Main Heading */}
          <div className="space-y-4">
            <h1 className="text-5xl font-bold tracking-tight text-foreground sm:text-6xl">
              Accelerate EGFR <span className="text-primary">Drug Discovery</span>
            </h1>
            <p className="text-xl text-muted-foreground">
              Harness the power of artificial intelligence and molecular docking to identify promising drug candidates. Secure, persistent, and team-ready.
            </p>
          </div>

          {/* CTA Buttons */}
          <div className="flex flex-col items-center justify-center gap-4 pt-8 sm:flex-row">
            <Link
              href="/dashboard"
              className="group inline-flex items-center justify-center gap-2 rounded-lg bg-primary px-8 py-4 font-semibold text-primary-foreground transition-transform hover:scale-105"
            >
              Go to Dashboard
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <Link
              href="/screening"
              className="inline-flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-8 py-4 font-semibold text-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
            >
              Start Screening
            </Link>
          </div>

          {/* Live Key Stats */}
          <div className="grid grid-cols-3 gap-4 pt-12 sm:gap-8">
            <div className="space-y-2">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 mb-2">
                <Database className="h-5 w-5 text-primary" />
              </div>
              <p className="text-2xl font-bold text-foreground sm:text-3xl">{stats.total_compounds}</p>
              <p className="text-sm text-muted-foreground">Compounds Screened</p>
            </div>
            <div className="space-y-2">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 mb-2">
                <Beaker className="h-5 w-5 text-primary" />
              </div>
              <p className="text-2xl font-bold text-foreground sm:text-3xl">{stats.total_runs}</p>
              <p className="text-sm text-muted-foreground">Screening Runs</p>
            </div>
            <div className="space-y-2">
              <div className="mx-auto flex h-10 w-10 items-center justify-center rounded-full bg-primary/10 mb-2">
                <Shield className="h-5 w-5 text-primary" />
              </div>
              <p className="text-2xl font-bold text-foreground sm:text-3xl">{stats.avg_pic50.toFixed(2)}</p>
              <p className="text-sm text-muted-foreground">Avg pIC50</p>
            </div>
          </div>

          {/* Recent Discovery Feed */}
          {recent.length > 0 && (
            <div className="pt-12 max-w-2xl mx-auto">
              <h3 className="text-sm font-semibold text-muted-foreground mb-4 uppercase tracking-wider">Latest Discoveries</h3>
              <div className="space-y-3">
                {recent.map((item, i) => (
                  <div key={i} className="flex items-center justify-between rounded-lg border border-border bg-card/50 px-4 py-3 text-sm">
                    <span className="font-medium text-foreground">{item.compound_id || 'Unknown'}</span>
                    <span className="text-muted-foreground">Scored <span className="text-primary font-bold">{item.pic50.toFixed(2)}</span> pIC50</span>
                    <span className="text-xs text-muted-foreground">{new Date(item.created_at).toLocaleDateString()}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </section>
  );
}
