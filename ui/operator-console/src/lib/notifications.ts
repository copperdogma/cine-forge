// Notification helpers wrapping Sonner toast API with CineForge-specific types.

import { toast } from 'sonner'

// --- Pipeline Notifications ---

export function notifyRunStarted(runId: string) {
  toast.info('Pipeline run started', {
    description: `Run ID: ${runId}`,
  })
}

export function notifyRunCompleted(runId: string, duration: string, cost: number) {
  toast.success('Pipeline run completed', {
    description: `${runId} • ${duration} • $${cost.toFixed(2)}`,
  })
}

export function notifyRunFailed(runId: string, error: string) {
  toast.error('Pipeline run failed', {
    description: `${runId}: ${error}`,
    duration: 10000,
  })
}

export function notifyStageCompleted(stageName: string, duration: string) {
  toast.success(`Stage "${stageName}" completed`, {
    description: `Finished in ${duration}`,
  })
}

// --- Artifact Notifications ---

export function notifyArtifactProduced(artifactType: string, entityId: string) {
  toast.success('Artifact produced', {
    description: `${artifactType} (${entityId})`,
  })
}

export function notifyArtifactStale(
  artifactType: string,
  entityId: string,
  onRerun?: () => void,
) {
  toast.warning('Artifact is stale', {
    description: `${artifactType} (${entityId}) is out of date`,
    action: onRerun
      ? {
          label: 'Re-run',
          onClick: onRerun,
        }
      : undefined,
    duration: 8000,
  })
}

// --- Review Notifications ---

export function notifyReviewReady(title: string, onOpen?: () => void) {
  toast.info('Review ready', {
    description: title,
    action: onOpen
      ? {
          label: 'Open',
          onClick: onOpen,
        }
      : undefined,
    duration: 10000,
  })
}

export function notifyReviewApproved(title: string) {
  toast.success('Review approved', {
    description: title,
  })
}

// --- General Notifications ---

export function notifyError(title: string, description?: string) {
  toast.error(title, {
    description,
    duration: 8000,
  })
}

export function notifySuccess(title: string, description?: string) {
  toast.success(title, {
    description,
  })
}

// --- Demo Hook ---

export function useNotificationDemo() {
  const fireDemo = () => {
    const runId = `demo-${Date.now()}`

    // t=0: Run started
    notifyRunStarted(runId)

    // t=1s: Stage "Ingest" completed
    setTimeout(() => {
      notifyStageCompleted('Ingest', '0.8s')
    }, 1000)

    // t=2s: Stage "Normalize" completed
    setTimeout(() => {
      notifyStageCompleted('Normalize', '1.2s')
    }, 2000)

    // t=3s: Artifact "screenplay_normalized" produced
    setTimeout(() => {
      notifyArtifactProduced('screenplay_normalized', 'project')
    }, 3000)

    // t=4s: Stage "Extract Entities" completed
    setTimeout(() => {
      notifyStageCompleted('Extract Entities', '2.1s')
    }, 4000)

    // t=5s: Run completed with cost summary
    setTimeout(() => {
      notifyRunCompleted(runId, '5.2s', 0.14)
    }, 5000)

    // t=6s: Review ready notification (demo actionable notification)
    setTimeout(() => {
      notifyReviewReady('Entity extraction results', () => {
        toast.info('Review opened (demo)')
      })
    }, 6000)
  }

  return { fireDemo }
}
