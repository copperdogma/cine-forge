import type { ChatAction, ProjectState } from './types'

export const CHAT_RUN_ACTION_IDS = {
  start_analysis: 'mvp_ingest',
  go_deeper: 'world_building',
} as const

type TrackedChatRunActionId = keyof typeof CHAT_RUN_ACTION_IDS

const LIVE_RUN_ACTION_STATES: Record<TrackedChatRunActionId, readonly ProjectState[]> = {
  start_analysis: ['fresh_import'],
  go_deeper: ['analyzed'],
}

function hasOwnKey<K extends string>(
  record: Record<K, unknown>,
  key: string,
): key is K {
  return Object.prototype.hasOwnProperty.call(record, key)
}

export function isTrackedChatRunActionId(actionId: string): actionId is TrackedChatRunActionId {
  return hasOwnKey(CHAT_RUN_ACTION_IDS, actionId)
}

function isMeaningfulAction(action: ChatAction): boolean {
  return Boolean(
    action.route
    || action.confirm_action
    || action.dismiss_action
    || action.retry_text
    || isTrackedChatRunActionId(action.id),
  )
}

export function isTrackedChatRunActionCurrent(
  actionId: TrackedChatRunActionId,
  projectState: ProjectState,
): boolean {
  return LIVE_RUN_ACTION_STATES[actionId].includes(projectState)
}

export function getChatActionPresentation(
  actions: ChatAction[] | undefined,
  projectState: ProjectState,
): { actions: ChatAction[]; archivedActionLabels: string[] } {
  if (!actions || actions.length === 0) {
    return { actions: [], archivedActionLabels: [] }
  }

  const archivedActionLabels: string[] = []
  const visibleActions: ChatAction[] = []

  for (const action of actions) {
    if (
      isTrackedChatRunActionId(action.id)
      && !isTrackedChatRunActionCurrent(action.id, projectState)
    ) {
      archivedActionLabels.push(action.label)
      continue
    }

    visibleActions.push(action)
  }

  return {
    actions: archivedActionLabels.length > 0
      ? visibleActions.filter(isMeaningfulAction)
      : visibleActions,
    archivedActionLabels,
  }
}
