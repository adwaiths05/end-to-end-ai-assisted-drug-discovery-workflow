'use client';

import { useState } from 'react';
import { Upload, Loader2, Filter } from 'lucide-react';
import { useScreeningContext } from '@/lib/context/ScreeningContext';
import { validateSmiles, submitScreening, uploadScreeningFile } from '@/lib/api/screening';

// The actual base models the backend runs (from artifact_loader.py and hybrid_ensemble.py)
const BACKEND_MODELS = ['RF', 'XGB', 'MPNN', 'GIN'] as const;
const ENSEMBLE_MODES = {
  hybrid: 'Hybrid (RF + XGB + MPNN + GIN)',
  gnn: 'GNN (MPNN + GIN)',
  classical: 'Classical (RF + XGB)',
  fallback: 'Fallback (mean)',
} as const;

interface ScreeningInputProps {
  onResultsReady: () => void;
}

export function ScreeningInput({ onResultsReady }: ScreeningInputProps) {
  const { setSession } = useScreeningContext();
  const [activeTab, setActiveTab] = useState<'single' | 'batch'>('single');
  const [singleSmiles, setSingleSmiles] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [validationResults, setValidationResults] = useState<{ smiles: string; valid: boolean; reason?: string | null }[] | null>(null);

  // Batch / CSV upload state
  const [batchFile, setBatchFile] = useState<File | null>(null);
  const [fileLoading, setFileLoading] = useState(false);
  const [batchSmiles, setBatchSmiles] = useState('');

  // Filter options (passed to POST /screening/batch)
  const [filterLipinski, setFilterLipinski] = useState(false);
  const [topN, setTopN] = useState<number | ''>('');
  const [showFilters, setShowFilters] = useState(false);

  // ─── Single SMILES ───────────────────────────────────────────────────────────

  const handleSingleSubmit = async () => {
    if (!singleSmiles.trim()) {
      setError('Please enter a SMILES string');
      return;
    }

    setLoading(true);
    setError(null);
    setValidationResults(null);

    try {
      // Validate SMILES structure via backend (RDKit check)
      const validations = await validateSmiles([singleSmiles]);
      setValidationResults(validations);

      // NOTE: The backend validate-smiles endpoint returns valid=false for BOTH:
      //   (a) Unparseable SMILES — reason: "Invalid SMILES"  → hard block
      //   (b) Lipinski failures  — reason: "LogP=5.1 > 5"   → warning only, proceed
      // Lipinski is drug-likeness, not structural validity.
      const isUnparseable = validations.some(v => !v.valid && v.reason === 'Invalid SMILES');

      if (isUnparseable) {
        setError('Invalid SMILES: RDKit could not parse this structure. Please check the SMILES syntax.');
        setLoading(false);
        return;
      }

      // Lipinski/drug-likeness warnings shown in validation panel but screening proceeds

      // Submit to backend
      const session = await submitScreening({ smiles: [singleSmiles] });
      setSession(session);
      onResultsReady();
    } catch (err) {
      console.error('[screening] Single submit error:', err);
      setError(`Screening failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // ─── Batch / File Upload ─────────────────────────────────────────────────────

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setBatchFile(file);
    setError(null);
  };

  const handleBatchSubmit = async () => {
    setLoading(true);
    setError(null);

    try {
      let session;

      if (batchFile) {
        // Use multipart upload endpoint: POST /screening/upload
        // Accepts CSV with columns: compound_id (optional), smiles
        session = await uploadScreeningFile(batchFile);
      } else if (batchSmiles.trim()) {
        // Parse pasted SMILES (one per line) and send to POST /screening/batch
        const smilesList = batchSmiles
          .split('\n')
          .map(s => s.trim())
          .filter(Boolean);

        if (smilesList.length === 0) {
          setError('No valid SMILES found in input');
          setLoading(false);
          return;
        }

        session = await submitScreening({
          smiles: smilesList,
          filter_lipinski: filterLipinski,
          top_n: topN !== '' ? Number(topN) : null,
        });
      } else {
        setError('Please upload a CSV file or paste SMILES strings');
        setLoading(false);
        return;
      }

      setSession(session);
      onResultsReady();
    } catch (err) {
      console.error('[screening] Batch error:', err);
      setError(`Batch screening failed: ${err instanceof Error ? err.message : 'Unknown error'}`);
    } finally {
      setLoading(false);
    }
  };

  // ─── Render ──────────────────────────────────────────────────────────────────

  return (
    <div className="space-y-6">
      {/* Ensemble Info Banner */}
      <div className="rounded-lg border border-primary/20 bg-primary/5 p-4">
        <p className="text-sm font-semibold text-foreground mb-1">Active Ensemble</p>
        <p className="text-xs text-muted-foreground">
          The backend automatically selects the best available ensemble from loaded model artifacts:
        </p>
        <div className="mt-2 flex flex-wrap gap-2">
          {BACKEND_MODELS.map(m => (
            <span key={m} className="rounded-full border border-primary/30 bg-primary/10 px-3 py-0.5 text-xs font-semibold text-primary">
              {m}
            </span>
          ))}
          <span className="rounded-full border border-border bg-muted px-3 py-0.5 text-xs text-muted-foreground">
            + Ridge meta-learner
          </span>
        </div>
      </div>

      {/* Tabs */}
      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <div className="flex gap-0 border-b border-border">
          <button
            id="tab-single"
            onClick={() => setActiveTab('single')}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === 'single'
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Single SMILES
          </button>
          <button
            id="tab-batch"
            onClick={() => setActiveTab('batch')}
            className={`flex-1 px-4 py-3 text-sm font-medium transition-colors ${
              activeTab === 'batch'
                ? 'border-b-2 border-primary text-primary'
                : 'text-muted-foreground hover:text-foreground'
            }`}
          >
            Batch / Upload
          </button>
        </div>

        <div className="p-6 space-y-4">
          {/* ── Single Tab ── */}
          {activeTab === 'single' && (
            <>
              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">
                  SMILES String
                </label>
                <textarea
                  id="smiles-input"
                  value={singleSmiles}
                  onChange={(e) => setSingleSmiles(e.target.value)}
                  placeholder="e.g., CC(=O)Oc1ccccc1C(=O)O"
                  className="w-full rounded-lg border border-border bg-muted px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                  rows={3}
                />
                <p className="text-xs text-muted-foreground">
                  SMILES will be validated by RDKit and standardized before screening. Predicts pIC50 against EGFR.
                </p>
              </div>
              <button
                id="btn-submit-single"
                onClick={handleSingleSubmit}
                disabled={loading}
                className="w-full rounded-lg bg-primary px-4 py-3 font-semibold text-primary-foreground transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? 'Screening…' : 'Run Screening'}
              </button>
            </>
          )}

          {/* ── Batch Tab ── */}
          {activeTab === 'batch' && (
            <>
              {/* CSV Upload */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">
                  Upload CSV File
                </label>
                <div className="relative rounded-lg border-2 border-dashed border-border bg-muted/50 p-8 text-center transition-colors hover:border-primary">
                  <input
                    id="file-upload"
                    type="file"
                    accept=".csv"
                    onChange={handleFileChange}
                    disabled={fileLoading}
                    className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                  />
                  <div className="space-y-2">
                    <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
                    <p className="text-sm font-medium text-foreground">
                      {batchFile ? batchFile.name : (fileLoading ? 'Loading…' : 'Drag and drop or click to upload')}
                    </p>
                    <p className="text-xs text-muted-foreground">
                      CSV with columns: <code className="text-primary">smiles</code> (required),{' '}
                      <code className="text-primary">compound_id</code> (optional)
                    </p>
                  </div>
                </div>
              </div>

              {/* Or paste SMILES */}
              <div className="space-y-2">
                <label className="block text-sm font-medium text-foreground">
                  Or Paste SMILES (one per line)
                </label>
                <textarea
                  id="batch-smiles-input"
                  value={batchSmiles}
                  onChange={(e) => setBatchSmiles(e.target.value)}
                  placeholder={"CC(=O)Oc1ccccc1C(=O)O\nc1ccccc1\nCCO"}
                  className="w-full rounded-lg border border-border bg-muted px-4 py-3 text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary font-mono text-sm"
                  rows={5}
                />
              </div>

              {/* Filter Options */}
              <div className="border-t border-border pt-4">
                <button
                  onClick={() => setShowFilters(!showFilters)}
                  className="flex items-center gap-2 text-sm font-medium text-foreground hover:text-primary transition-colors"
                >
                  <Filter className="h-4 w-4" />
                  {showFilters ? 'Hide' : 'Show'} Filters
                </button>

                {showFilters && (
                  <div className="mt-4 space-y-3 rounded-lg border border-border bg-muted/30 p-4">
                    <label className="flex items-center gap-3 cursor-pointer">
                      <input
                        id="filter-lipinski"
                        type="checkbox"
                        checked={filterLipinski}
                        onChange={(e) => setFilterLipinski(e.target.checked)}
                        className="rounded border-border"
                      />
                      <div>
                        <p className="text-sm font-medium text-foreground">Apply Lipinski Rule of 5</p>
                        <p className="text-xs text-muted-foreground">MW ≤ 500, LogP ≤ 5, HBD ≤ 5, HBA ≤ 10</p>
                      </div>
                    </label>

                    <div className="space-y-1">
                      <label className="block text-sm font-medium text-foreground">
                        Return top-N results
                      </label>
                      <input
                        id="top-n-input"
                        type="number"
                        min={1}
                        value={topN}
                        onChange={(e) => setTopN(e.target.value === '' ? '' : Number(e.target.value))}
                        placeholder="All results"
                        className="w-full rounded-lg border border-border bg-card px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
                      />
                    </div>
                  </div>
                )}
              </div>

              <button
                id="btn-submit-batch"
                onClick={handleBatchSubmit}
                disabled={loading || (!batchFile && !batchSmiles.trim())}
                className="w-full rounded-lg bg-primary px-4 py-3 font-semibold text-primary-foreground transition-all hover:scale-105 disabled:opacity-50 disabled:hover:scale-100 flex items-center justify-center gap-2"
              >
                {loading && <Loader2 className="h-4 w-4 animate-spin" />}
                {loading ? 'Screening…' : 'Run Batch Screening'}
              </button>
            </>
          )}
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="rounded-lg border border-destructive/30 bg-destructive/10 p-4">
          <p className="text-sm text-destructive">{error}</p>
        </div>
      )}

      {/* Validation Results */}
      {validationResults && (
        <div className={`rounded-lg border p-4 ${
          validationResults.some(v => !v.valid && v.reason === 'Invalid SMILES')
            ? 'border-destructive/30 bg-destructive/10'
            : validationResults.some(v => !v.valid)
            ? 'border-yellow-500/30 bg-yellow-500/10'
            : 'border-green-500/30 bg-green-500/10'
        }`}>
          <p className="text-sm font-medium text-foreground mb-2">Validation</p>
          {validationResults.map((result, idx) => {
            const isStructuralError = !result.valid && result.reason === 'Invalid SMILES';
            const isLipinskiWarning = !result.valid && result.reason !== 'Invalid SMILES';
            return (
              <div key={idx} className="text-xs space-y-0.5">
                <div className="flex items-start gap-1.5">
                  <span className={
                    result.valid ? 'text-green-500' :
                    isLipinskiWarning ? 'text-yellow-500' : 'text-destructive'
                  }>
                    {result.valid ? '✓' : isLipinskiWarning ? '⚠' : '✗'}
                  </span>
                  <span className="font-mono text-muted-foreground truncate max-w-sm">{result.smiles}</span>
                </div>
                {result.reason && (
                  <p className={`pl-4 ${isLipinskiWarning ? 'text-yellow-600 dark:text-yellow-400' : 'text-destructive'}`}>
                    {isLipinskiWarning
                      ? `⚠ Drug-likeness note: ${result.reason} (Lipinski Ro5 — screening will still proceed)`
                      : result.reason}
                  </p>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
