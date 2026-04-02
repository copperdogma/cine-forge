import type { ChatAction, ChatCharacter, ChatMessage, PreflightData } from '../types'
import { API_BASE, ApiRequestError, request } from './core'

export interface ChatStreamChunk {
  type:
    | 'text'
    | 'tool_start'
    | 'tool_result'
    | 'actions'
    | 'role_start'
    | 'role_done'
    | 'context_info'
    | 'injected_content'
    | 'done'
    | 'error'
  content?: string
  name?: string
  id?: string
  speaker?: string
  display_name?: string
  model?: string
  actions?: ChatAction[]
  preflight_data?: PreflightData
}

type StreamHandlers = {
  onChunk: (chunk: ChatStreamChunk) => void
  onDone: () => void
  onError: (error: Error) => void
}

async function streamJsonEvents(
  path: string,
  payload: Record<string, unknown>,
  { onChunk, onDone, onError }: StreamHandlers,
  signal?: AbortSignal,
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}${path}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal,
    })

    if (!response.ok) {
      const text = await response.text()
      throw new ApiRequestError(`Stream failed (${response.status}): ${text}`)
    }

    const reader = response.body?.getReader()
    if (!reader) throw new Error('No stream reader')

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue

        const dataStr = line.slice(6)
        try {
          const chunk = JSON.parse(dataStr) as ChatStreamChunk
          if (chunk.type === 'done') {
            onDone()
            return
          }
          if (chunk.type === 'error') {
            onError(new Error(chunk.content ?? 'Stream error'))
            return
          }
          onChunk(chunk)
        } catch {
          // Skip malformed chunks.
        }
      }
    }

    onDone()
  } catch (error) {
    onError(error instanceof Error ? error : new Error('Stream failed'))
  }
}

export function getChatMessages(projectId: string): Promise<ChatMessage[]> {
  return request<ChatMessage[]>(`/api/projects/${projectId}/chat`)
}

export function postChatMessage(projectId: string, message: ChatMessage): Promise<ChatMessage> {
  return request<ChatMessage>(`/api/projects/${projectId}/chat`, {
    method: 'POST',
    body: JSON.stringify(message),
  })
}

export function listProjectCharacters(projectId: string): Promise<ChatCharacter[]> {
  return request<ChatCharacter[]>(`/api/projects/${projectId}/characters`)
}

export function streamChatMessage(
  projectId: string,
  message: string,
  messageId: string,
  chatHistory: Array<{ type: string; content: string; speaker?: string }>,
  onChunk: (chunk: ChatStreamChunk) => void,
  onDone: () => void,
  onError: (error: Error) => void,
  pageContext?: string,
  activeRole?: string,
  signal?: AbortSignal,
): Promise<void> {
  return streamJsonEvents(
    `/api/projects/${projectId}/chat/stream`,
    {
      message,
      message_id: messageId,
      chat_history: chatHistory,
      ...(pageContext ? { page_context: pageContext } : {}),
      ...(activeRole ? { active_role: activeRole } : {}),
    },
    { onChunk, onDone, onError },
    signal,
  )
}

export function streamAutoInsight(
  projectId: string,
  trigger: string,
  context: Record<string, unknown>,
  onChunk: (chunk: ChatStreamChunk) => void,
  onDone: () => void,
  onError: (error: Error) => void,
): Promise<void> {
  return streamJsonEvents(
    `/api/projects/${projectId}/chat/insight`,
    { trigger, context },
    { onChunk, onDone, onError },
  )
}
