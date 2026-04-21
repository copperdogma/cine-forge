import { useEffect } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getChatMessages, listProjectCharacters } from '../api'
import { shouldAttemptChatLoad } from '../chat-load-state'
import {
  areBootstrapMessagesCurrent,
  getWelcomeMessages,
  hasOnlyBootstrapMessages,
} from '../chat-messages'
import { useChatStore } from '../chat-store'
import type { ChatCharacter } from '../types'
import { useProject, useProjectState } from './projects'

export function useProjectCharacters(projectId: string | undefined) {
  return useQuery<ChatCharacter[]>({
    queryKey: ['projects', projectId, 'characters'],
    queryFn: () => listProjectCharacters(projectId!),
    enabled: !!projectId,
    staleTime: 60_000,
  })
}

export function useChatLoader(projectId: string | undefined) {
  const projectState = useProjectState(projectId)
  const { data: project, isLoading } = useProject(projectId)
  const chatLoadState = useChatStore((store) =>
    projectId ? store.getChatLoadState(projectId) : undefined,
  )

  useEffect(() => {
    if (!projectId || !project || isLoading) return
    const welcomeMessages = getWelcomeMessages(projectState, project)

    const store = useChatStore.getState()
    const replaceBootstrapMessages = (
      messages: typeof welcomeMessages,
      options?: { loaded?: boolean },
    ) => {
      store.seedLocalMessages(projectId, messages, options)
    }

    if (chatLoadState?.phase === 'ready') {
      const loadedMessages = store.getMessages(projectId)
      if (
        hasOnlyBootstrapMessages(loadedMessages)
        && !areBootstrapMessagesCurrent(loadedMessages, projectState, project)
      ) {
        replaceBootstrapMessages(welcomeMessages, { loaded: store.isLoaded(projectId) })
      }
      return
    }

    if (!shouldAttemptChatLoad(chatLoadState)) {
      return
    }

    store.beginChatLoad(projectId)
    getChatMessages(projectId)
      .then((backendMessages) => {
        if (useChatStore.getState().isLoaded(projectId)) return
        if (backendMessages.length > 0 && !hasOnlyBootstrapMessages(backendMessages)) {
          useChatStore.getState().loadMessages(projectId, backendMessages)
        } else {
          replaceBootstrapMessages(welcomeMessages, { loaded: true })
          useChatStore.getState().setChatLoadReady(projectId)
        }
      })
      .catch((error) => {
        const currentStore = useChatStore.getState()
        if (!currentStore.hasMessages(projectId)) {
          replaceBootstrapMessages(welcomeMessages)
        }
        currentStore.setChatLoadError(projectId, error)
      })
  }, [projectId, projectState, project, isLoading, chatLoadState])
}
