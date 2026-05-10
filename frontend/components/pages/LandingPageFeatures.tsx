'use client';

import { Zap, BarChart3, Microscope, Database, Eye, Cpu, Shield, Clock } from 'lucide-react';

const features = [
  {
    icon: Zap,
    title: 'Rapid Screening',
    description: 'Evaluate thousands of SMILES strings in minutes using a 4-model ensemble (RF, XGB, MPNN, GIN) with Ridge meta-learner.',
  },
  {
    icon: Microscope,
    title: 'Molecular Docking',
    description: 'Run AutoDock Vina simulations with real-time progress tracking and configurable parameters.',
  },
  {
    icon: Database,
    title: 'Persistent History',
    description: 'All screening runs and docking simulations are securely saved in a PostgreSQL database for team access and review.',
  },
  {
    icon: BarChart3,
    title: 'Comprehensive Analysis',
    description: 'Analyze interaction profiles, consensus rankings, and model divergence across multiple dimensions.',
  },
  {
    icon: Shield,
    title: 'Secure Authentication',
    description: 'JWT-based researcher authentication keeps your proprietary molecular data secure and private.',
  },
  {
    icon: Cpu,
    title: 'ML-Powered Consensus',
    description: 'Get ensemble pIC50 predictions with robust uncertainty quantification and cross-model agreement scores.',
  },
];

const steps = [
  {
    number: 1,
    title: 'Secure Login',
    description: 'Authenticate to access your secure workspace and run history',
  },
  {
    number: 2,
    title: 'ML Screening',
    description: 'Run batch screening with 4 base models + Ridge ensemble',
  },
  {
    number: 3,
    title: 'Docking & Save',
    description: 'Submit top hits to Vina, auto-saved to your Neon database',
  },
  {
    number: 4,
    title: 'Analyze & Share',
    description: 'Explore interactions and share results with your research team',
  },
];

export function LandingPageFeatures() {
  return (
    <section className="relative space-y-24 py-20 sm:py-28">
      {/* Features Grid */}
      <div className="container mx-auto px-4">
        <div className="mb-16 space-y-4 text-center">
          <h2 id="how-it-works" className="text-4xl font-bold text-foreground">
            Deploy-Ready Features
          </h2>
          <p className="text-lg text-muted-foreground">
            Everything you need for advanced, collaborative drug screening
          </p>
        </div>

        <div className="grid gap-8 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => {
            const Icon = feature.icon;
            return (
              <div
                key={index}
                className="group rounded-xl border border-border bg-card p-6 transition-all hover:border-primary/50 hover:bg-card"
              >
                <div className="mb-4 inline-block rounded-lg bg-primary/10 p-3">
                  <Icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">{feature.title}</h3>
                <p className="text-muted-foreground">{feature.description}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* How It Works */}
      <div className="container mx-auto px-4">
        <div className="mb-16 space-y-4 text-center">
          <h2 className="text-4xl font-bold text-foreground">Collaborative Workflow</h2>
          <p className="text-lg text-muted-foreground">
            A streamlined, persistent workflow from input to analysis
          </p>
        </div>

        <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
          {steps.map((step, index) => (
            <div key={index} className="relative">
              {/* Connector Line */}
              {index < steps.length - 1 && (
                <div className="absolute -right-3 top-8 hidden h-0.5 w-6 bg-primary/30 lg:block" />
              )}

              <div className="relative space-y-4">
                <div className="flex h-12 w-12 items-center justify-center rounded-full border-2 border-primary bg-primary/10">
                  <span className="font-bold text-primary">{step.number}</span>
                </div>
                <div>
                  <h3 className="font-semibold text-foreground">{step.title}</h3>
                  <p className="text-sm text-muted-foreground">{step.description}</p>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
