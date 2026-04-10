import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getChatMessages, listProjectCharacters } from '../api'
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
  const initializedRef = useRef<string | null>(null)

  useEffect(() => {
    if (!projectId || !project || isLoading) return
    const welcomeMessages = getWelcomeMessages(projectState, project)

    const store = useChatStore.getState()
    const replaceBootstrapMessages = (messages: typeof welcomeMessages) => {
      store.loadMessages(projectId, [])
      for (const message of messages) {
        store.addMessage(projectId, message)
      }
    }

    if (initializedRef.current === projectId) {
      if (store.isLoaded(projectId)) {
        const loadedMessages = store.getMessages(projectId)
        if (
          hasOnlyBootstrapMessages(loadedMessages)
          && !areBootstrapMessagesCurrent(loadedMessages, projectState, project)
        ) {
          replaceBootstrapMessages(welcomeMessages)
        }
      }
      return
    }

    if (store.isLoaded(projectId)) {
      const loadedMessages = store.getMessages(projectId)
      if (
        hasOnlyBootstrapMessages(loadedMessages)
        && !areBootstrapMessagesCurrent(loadedMessages, projectState, project)
      ) {
        replaceBootstrapMessages(welcomeMessages)
      }
      initializedRef.current = projectId
      return
    }

    initializedRef.current = projectId
    getChatMessages(projectId)
      .then((backendMessages) => {
        if (useChatStore.getState().isLoaded(projectId)) return
        if (backendMessages.length > 0 && !hasOnlyBootstrapMessages(backendMessages)) {
          useChatStore.getState().loadMessages(projectId, backendMessages)
        } else {
          replaceBootstrapMessages(welcomeMessages)
        }
      })
      .catch(() => {
        const currentStore = useChatStore.getState()
        if (!currentStore.hasMessages(projectId)) {
          replaceBootstrapMessages(welcomeMessages)
        }
      })
  }, [projectId, projectState, project, isLoading])
}
