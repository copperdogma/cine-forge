import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2 } from 'lucide-react'
import { toast } from 'sonner'
import { Button } from '@/components/ui/button'
import { useChatStore } from '@/lib/chat-store'
import { getRunningRunLabel } from '@/lib/constants'
import { useActiveProjectRun } from '@/lib/hooks'
import { startTrackedRun } from '@/lib/run-actions'
import type { ChatAction, ChatMessage, RunStartPayload } from '@/lib/types'
import { RUN_ACTION_IDS } from './config'

export type StartRunAction = {
  mutateAsync: (payload: RunStartPayload) => Promise<{ run_id: string }>
  isPending: boolean
}

type ActionButtonProps = {
  action: ChatAction
  messageId: string
  projectId: string
  startRun: StartRunAction
  inputPath: string | undefined
  onRetry?: (text: string) => void
}

function extractEditEntityId(endpoint: string): string | undefined {
  const parts = endpoint.split('/').filter(Boolean)
  const editIndex = parts.lastIndexOf('edit')
  if (editIndex < 2) return undefined
  return parts[editIndex - 1]
}

export function ActionButton({
  action,
  messageId,
  projectId,
  startRun,
  inputPath,
  onRetry,
}: ActionButtonProps) {
  const navigate = useNavigate()
  const [busy, setBusy] = useState(false)
  const { isRunning: hasActiveRun, recipeId: activeRecipeId } = useActiveProjectRun(projectId)
  const isRunAction = !!RUN_ACTION_IDS[action.id] || action.confirm_action?.type === 'start_run'

  const handleClick = async () => {
    if (isRunAction && hasActiveRun) return
    const store = useChatStore.getState()

    const recordUserAction = () => {
      const message: ChatMessage = {
        id: `action_${Date.now()}`,
        type: 'user_action',
        content: action.label,
        timestamp: Date.now(),
        resolvedMessageId: messageId,
      }
      store.addMessage(projectId, message)
    }

    const recordLocalUserAction = () => {
      const message: ChatMessage = {
        id: `action_${Date.now()}`,
        type: 'user_action',
        content: action.label,
        timestamp: Date.now(),
        resolvedMessageId: messageId,
      }
      store.addLocalMessage(projectId, message)
    }

    if (action.retry_text && onRetry) {
      recordUserAction()
      onRetry(action.retry_text)
      return
    }

    if (action.dismiss_action) {
      store.dismissMessageActions(projectId, messageId)
      recordLocalUserAction()
      return
    }

    if (action.confirm_action) {
      setBusy(true)
      recordUserAction()

      try {
        const response = await fetch(action.confirm_action.endpoint, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(action.confirm_action.payload),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => null)
          throw new Error(errorData?.message ?? `Request failed (${response.status})`)
        }

        const result = await response.json()

        if (action.confirm_action.type === 'start_run' && result.run_id) {
          store.setActiveRun(projectId, result.run_id)
          store.addMessage(projectId, {
            id: `run_started_${result.run_id}`,
            type: 'ai_status',
            content: 'Run started — processing your project now...',
            timestamp: Date.now(),
            actions: [
              { id: 'view_run', label: 'View Run Details', variant: 'outline', route: `runs/${result.run_id}` },
            ],
          })
          store.addActivity(projectId, 'Started pipeline run', `runs/${result.run_id}`)
        } else if (action.confirm_action.type === 'edit_artifact') {
          const routeEntityId = result.entity_id ?? extractEditEntityId(action.confirm_action.endpoint)
          const entityLabel = routeEntityId === '__project__' ? 'project' : (routeEntityId ?? 'unknown')
          const artLabel = `${result.artifact_type ?? 'artifact'}/${entityLabel}`
          const artRoute = result.artifact_type && routeEntityId
            ? `artifacts/${result.artifact_type}/${routeEntityId}/${result.version ?? 1}`
            : undefined
          store.addMessage(projectId, {
            id: `edit_done_${Date.now()}`,
            type: 'ai_status_done',
            content: `Changes applied — created version ${result.version ?? 'new'} of ${artLabel}.`,
            timestamp: Date.now(),
            actions: artRoute
              ? [{ id: 'view_artifact', label: 'View Artifact', variant: 'outline', route: artRoute }]
              : undefined,
          })
          store.addActivity(projectId, `Updated: ${artLabel}`, artRoute)
        }
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Action failed'
        toast.error(message)
        store.addMessage(projectId, {
          id: `error_${Date.now()}`,
          type: 'ai_suggestion',
          content: `Something went wrong: ${message}. You can try again or ask the AI for help.`,
          timestamp: Date.now(),
        })
      } finally {
        setBusy(false)
      }
      return
    }

    const recipeId = RUN_ACTION_IDS[action.id]

    if (recipeId && inputPath) {
      setBusy(true)
      try {
        await startTrackedRun({
          projectId,
          actionLabel: action.label,
          startRun: startRun.mutateAsync,
          payload: {
            project_id: projectId,
            input_file: inputPath,
            default_model: 'claude-sonnet-4-6',
            recipe_id: recipeId,
            accept_config: true,
          },
        })
      } catch (error) {
        const message = error instanceof Error ? error.message : 'Failed to start analysis'
        toast.error(message)
        const store = useChatStore.getState()
        store.addMessage(projectId, {
          id: `error_${Date.now()}`,
          type: 'ai_suggestion',
          content: `Something went wrong: ${message}. You can try again or configure the pipeline manually.`,
          timestamp: Date.now(),
          actions: [
            { id: 'manual_pipeline', label: 'Configure Manually', variant: 'outline', route: 'run' },
          ],
        })
      } finally {
        setBusy(false)
      }
      return
    }

    if (action.route) {
      if (action.route.startsWith('/')) {
        navigate(action.route)
      } else {
        navigate(`/${projectId}/${action.route}`)
      }
    }
  }

  return (
    <Button
      variant={action.variant === 'default' ? 'default' : action.variant === 'secondary' ? 'secondary' : 'outline'}
      size="sm"
      className="cursor-pointer"
      onClick={handleClick}
      disabled={busy || startRun.isPending || (isRunAction && hasActiveRun)}
    >
      {busy ? (
        <>
          <Loader2 className="h-3 w-3 mr-1.5 animate-spin" />
          Starting...
        </>
      ) : isRunAction && hasActiveRun ? (
        getRunningRunLabel(activeRecipeId)
      ) : (
        action.label
      )}
    </Button>
  )
}
