'use client';

import { useState } from 'react';
import { ScreeningInput } from '@/components/pages/ScreeningInput';
import { ScreeningResults } from '@/components/pages/ScreeningResults';
import { useRouter } from 'next/navigation';

export default function ScreeningPage() {
  const router = useRouter();
  const [showResults, setShowResults] = useState(false);

  const handleProceedToDocking = () => {
    router.push('/docking');
  };

  return (
    <div className="container mx-auto px-4 py-12">
      <div className="max-w-4xl mx-auto space-y-12">
        {/* Page Header */}
        <div className="space-y-4">
          <h1 className="text-4xl font-bold text-foreground">Virtual Screening</h1>
          <p className="text-lg text-muted-foreground">
            Predict EGFR inhibitor potency (pIC50) using a hybrid ensemble of Random Forest, XGBoost, MPNN, and GIN models with a Ridge meta-learner.
          </p>
        </div>

        {/* Input or Results */}
        {!showResults ? (
          <ScreeningInput onResultsReady={() => setShowResults(true)} />
        ) : (
          <>
            <div className="flex items-center gap-4">
              <button
                onClick={() => setShowResults(false)}
                className="rounded-lg border border-border bg-card px-4 py-2 font-medium text-foreground transition-colors hover:bg-accent"
              >
                ← Back to Input
              </button>
            </div>
            <ScreeningResults onProceedToDocking={handleProceedToDocking} />
          </>
        )}
      </div>
    </div>
  );
}
