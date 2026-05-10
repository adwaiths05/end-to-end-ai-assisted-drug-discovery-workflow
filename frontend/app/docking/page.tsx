'use client';

import { useState } from 'react';
import { useScreeningContext } from '@/lib/context/ScreeningContext';
import { useDockingContext } from '@/lib/context/DockingContext';
import { DockingConfiguration, DockingParameters } from '@/components/pages/DockingConfiguration';
import { DockingProgress } from '@/components/pages/DockingProgress';
import { DockingResults } from '@/components/pages/DockingResults';
import { submitDockingJob } from '@/lib/api/docking';
import { useRouter } from 'next/navigation';

export default function DockingPage() {
  const router = useRouter();
  const { session: screeningSession } = useScreeningContext();
  const { job, setJob, clearJob } = useDockingContext();
  
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Derive top hits from screening session using predicted_pic50 (real backend field)
  const topHits = screeningSession
    ? [...screeningSession.results]
        .filter(r => r.valid && r.predicted_pic50 != null)
        .sort((a, b) => (b.predicted_pic50 ?? 0) - (a.predicted_pic50 ?? 0))
        .slice(0, 10)
    : [];

  if (!screeningSession) {
    return (
      <div className="container mx-auto px-4 py-12">
        <div className="max-w-4xl mx-auto space-y-8">
          <div className="rounded-lg border border-border bg-card p-8 text-center space-y-4">
            <h2 className="text-2xl font-bold text-foreground">No Screening Data</h2>
            <p className="text-muted-foreground">
              Please complete the screening step first to proceed with docking.
            </p>
            <button
              onClick={() => router.push('/screening')}
              className="inline-flex rounded-lg bg-primary px-6 py-3 font-semibold text-primary-foreground transition-all hover:scale-105"
            >
              Go to Screening
            </button>
          </div>
        </div>
      </div>
    );
  }

  const handleSubmitDocking = async (
    selectedCompounds: typeof topHits,
    parameters: DockingParameters
  ) => {
    setIsSubmitting(true);
    setError(null);

    try {
      const newJob = await submitDockingJob({
        smiles: selectedCompounds.map(c => c.canonical_smiles || c.smiles),
        predicted_pic50: selectedCompounds.map(c => c.predicted_pic50 ?? 0),
        compound_ids: selectedCompounds.map((c, i) => c.compoundId || `lig_${String(i).padStart(3, '0')}`),
        uiParameters: parameters,
      });
      setJob(newJob);
    } catch (err) {
      console.error('[docking] Submission error:', err);
      setError(`Failed to submit docking job: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setIsSubmitting(false);
    }
  };


  const handleViewAnalysis = () => {
    router.push('/analysis');
  };

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Page Header */}
        <div className="space-y-4">
          <h1 className="text-4xl font-bold text-foreground">Molecular Docking</h1>
          <p className="text-lg text-muted-foreground">
            Configure and run AutoDock Vina simulations on your screening hits.
          </p>
        </div>

        {error && (
          <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4">
            <p className="text-sm text-destructive">{error}</p>
          </div>
        )}

        {/* Show Configuration or Progress */}
        {!job ? (
          <DockingConfiguration
            topHits={topHits}
            onSubmit={handleSubmitDocking}
            isLoading={isSubmitting}
          />
        ) : (
          <div className="space-y-6">
            <DockingProgress
              job={job}
              onPause={() => {}}
              onResume={() => {}}
              onCancel={clearJob}
              isPaused={false}
            />

            <DockingResults results={job.results} />

            {job.status === 'completed' && (
              <div className="flex flex-col gap-4 sm:flex-row">
                <button
                  onClick={clearJob}
                  className="w-full rounded-lg border border-border bg-card px-6 py-4 font-semibold text-foreground transition-all hover:bg-muted"
                >
                  Re-configure Docking
                </button>
                <button
                  onClick={handleViewAnalysis}
                  className="w-full rounded-lg bg-primary px-6 py-4 font-semibold text-primary-foreground transition-all hover:scale-105"
                >
                  Proceed to Analysis
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
