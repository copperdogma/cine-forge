import { useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { getChatMessages, listProjectCharacters } from '../api'
import { getWelcomeMessages } from '../chat-messages'
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
    if (initializedRef.current === projectId) return

    const store = useChatStore.getState()
    if (store.isLoaded(projectId)) {
      initializedRef.current = projectId
      return
    }

    initializedRef.current = projectId
    getChatMessages(projectId)
      .then((backendMessages) => {
        if (useChatStore.getState().isLoaded(projectId)) return
        if (backendMessages.length > 0) {
          useChatStore.getState().loadMessages(projectId, backendMessages)
        } else {
          const welcomeMessages = getWelcomeMessages(projectState, project)
          useChatStore.getState().loadMessages(projectId, [])
          for (const message of welcomeMessages) {
            useChatStore.getState().addMessage(projectId, message)
          }
        }
      })
      .catch(() => {
        const currentStore = useChatStore.getState()
        if (!currentStore.hasMessages(projectId)) {
          const welcomeMessages = getWelcomeMessages(projectState, project)
          currentStore.loadMessages(projectId, welcomeMessages)
        }
      })
  }, [projectId, projectState, project, isLoading])
}
