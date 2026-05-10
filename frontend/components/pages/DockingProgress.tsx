'use client';

import { DockingJob } from '@/lib/context/DockingContext';
import { Pause, Play, X } from 'lucide-react';

interface DockingProgressProps {
  job: DockingJob;
  onPause: () => void;
  onResume: () => void;
  onCancel: () => void;
  isPaused: boolean;
}

export function DockingProgress({
  job,
  onPause,
  onResume,
  onCancel,
  isPaused,
}: DockingProgressProps) {
  const formatTime = (seconds: number) => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = seconds % 60;

    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    } else if (minutes > 0) {
      return `${minutes}m ${secs}s`;
    } else {
      return `${secs}s`;
    }
  };

  const isComplete = job.status === 'completed';
  const isFailed = job.status === 'failed';

  return (
    <div className="space-y-6 rounded-lg border border-border bg-card p-6">
      {/* Status Header */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-semibold text-foreground">Docking Progress</h3>
          <div className="flex items-center gap-2">
            <span
              className={`inline-block h-3 w-3 rounded-full ${
                isFailed
                  ? 'bg-destructive'
                  : isComplete
                  ? 'bg-primary'
                  : isPaused
                  ? 'bg-yellow-500'
                  : 'bg-primary animate-pulse'
              }`}
            />
            <span className="text-sm font-medium text-muted-foreground">
              {isFailed ? 'Failed' : isComplete ? 'Complete' : isPaused ? 'Paused' : 'Processing'}
            </span>
          </div>
        </div>
        <p className="text-sm text-muted-foreground">Job ID: {job.jobId}</p>
      </div>

      {/* Current Compound */}
      <div className="space-y-2">
        <p className="text-sm font-medium text-foreground">Current Compound</p>
        <p className="text-lg text-primary font-semibold">{job.currentCompound || 'Initializing...'}</p>
      </div>

      {/* Progress Bar */}
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-foreground">Overall Progress</p>
          <span className="text-sm font-semibold text-primary">{job.progress}%</span>
        </div>
        <div className="h-3 rounded-full bg-muted overflow-hidden">
          <div
            className="h-full bg-gradient-to-r from-primary to-primary/50 transition-all duration-500"
            style={{ width: `${job.progress}%` }}
          />
        </div>
      </div>

      {/* Statistics */}
      <div className="grid gap-4 sm:grid-cols-3">
        <div className="rounded-lg border border-border bg-muted/50 p-4">
          <p className="text-xs text-muted-foreground">Progress</p>
          <p className="text-2xl font-bold text-primary">{job.progress}%</p>
        </div>
        <div className="rounded-lg border border-border bg-muted/50 p-4">
          <p className="text-xs text-muted-foreground">ETA</p>
          <p className="text-2xl font-bold text-primary">{formatTime(job.eta)}</p>
        </div>
        <div className="rounded-lg border border-border bg-muted/50 p-4">
          <p className="text-xs text-muted-foreground">Results</p>
          <p className="text-2xl font-bold text-primary">{job.results.length}</p>
        </div>
      </div>

      {/* Docking Parameters */}
      <div className="rounded-lg border border-border bg-muted/30 p-4 space-y-2">
        <p className="text-sm font-medium text-foreground">Parameters</p>
        <div className="grid grid-cols-2 gap-3 text-xs text-muted-foreground">
          <div>Exhaustiveness: <span className="text-foreground font-semibold">{job.parameters.exhaustiveness}</span></div>
          <div>Poses: <span className="text-foreground font-semibold">{job.parameters.poses}</span></div>
          <div>CPU Threads: <span className="text-foreground font-semibold">{job.parameters.cpuThreads}</span></div>
          <div>Grid: <span className="text-foreground font-semibold">{job.parameters.gridSpacing?.toFixed(3)} Å</span></div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="flex gap-3 pt-4 border-t border-border">
        {!isComplete && !isFailed && (
          <>
            {isPaused ? (
              <button
                onClick={onResume}
                className="flex-1 flex items-center justify-center gap-2 rounded-lg bg-primary px-4 py-3 font-semibold text-primary-foreground transition-all hover:scale-105"
              >
                <Play className="h-4 w-4" />
                Resume
              </button>
            ) : (
              <button
                onClick={onPause}
                className="flex-1 flex items-center justify-center gap-2 rounded-lg border border-border bg-card px-4 py-3 font-semibold text-foreground transition-colors hover:bg-accent"
              >
                <Pause className="h-4 w-4" />
                Pause
              </button>
            )}

            <button
              onClick={onCancel}
              className="flex-1 flex items-center justify-center gap-2 rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 font-semibold text-destructive transition-colors hover:bg-destructive/20"
            >
              <X className="h-4 w-4" />
              Cancel
            </button>
          </>
        )}

        {isComplete && (
          <div className="w-full rounded-lg border border-primary/30 bg-primary/10 px-4 py-3 text-center">
            <p className="font-semibold text-primary">Docking completed successfully!</p>
          </div>
        )}

        {isFailed && (
          <div className="w-full rounded-lg border border-destructive/30 bg-destructive/10 px-4 py-3 text-center">
            <p className="font-semibold text-destructive">Docking failed. Please try again.</p>
          </div>
        )}
      </div>
    </div>
  );
}
