'use client';

import { BarChart3, Database, Cpu, Eye } from 'lucide-react';

const technologies = [
  {
    icon: Cpu,
    name: 'ML Models',
    items: ['Random Forest (RF)', 'XGBoost (XGB)', 'MPNN (EdgeAware GNN)', 'GIN (Graph Isomorphism Net)', 'Ridge Meta-Learner'],
  },
  {
    icon: Database,
    name: 'Molecular Docking',
    items: ['AutoDock Vina', 'PDBQT Format', 'Grid-based Search', 'Scoring Functions'],
  },
  {
    icon: Eye,
    name: '3D Visualization',
    items: ['Mol*', 'PDB Structures', 'Protein Cartoons', 'Ligand Models'],
  },
  {
    icon: BarChart3,
    name: 'Analysis',
    items: ['H-Bond Detection', 'π-Stacking', 'Hydrophobic Interactions', 'Consensus Scoring'],
  },
];

export function LandingPageTechStack() {
  return (
    <section className="border-t border-border bg-muted/30 py-20 sm:py-28">
      <div className="container mx-auto px-4">
        <div className="mb-16 space-y-4 text-center">
          <h2 className="text-4xl font-bold text-foreground">Technology Stack</h2>
          <p className="text-lg text-muted-foreground">
            Built on industry-standard tools and cutting-edge AI models
          </p>
        </div>

        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-4">
          {technologies.map((tech, index) => {
            const Icon = tech.icon;
            return (
              <div
                key={index}
                className="rounded-xl border border-border bg-card p-6"
              >
                <div className="mb-4 flex items-center gap-3">
                  <div className="rounded-lg bg-primary/10 p-2">
                    <Icon className="h-5 w-5 text-primary" />
                  </div>
                  <h3 className="font-semibold text-foreground">{tech.name}</h3>
                </div>
                <ul className="space-y-2">
                  {tech.items.map((item, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm text-muted-foreground">
                      <span className="mt-1.5 h-1 w-1 rounded-full bg-primary flex-shrink-0" />
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            );
          })}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 rounded-xl border border-primary/30 bg-primary/5 p-8 text-center">
          <h3 className="mb-4 text-2xl font-bold text-foreground">Ready to discover new drugs?</h3>
          <p className="mb-6 text-muted-foreground">
            Start with our AI-powered screening and docking pipeline
          </p>
          <a
            href="/screening"
            className="inline-flex items-center justify-center rounded-lg bg-primary px-8 py-3 font-semibold text-primary-foreground transition-transform hover:scale-105"
          >
            Begin Screening
          </a>
        </div>
      </div>
    </section>
  );
}
