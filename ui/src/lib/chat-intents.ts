export const CHAT_INTENT_EVENT = 'cineforge:chat-intent'

export type ChatIntent =
  | { mode: 'send'; text: string }
  | { mode: 'draft'; text: string }

let pendingIntent: ChatIntent | null = null

export function dispatchChatIntent(intent: ChatIntent) {
  pendingIntent = intent
  window.dispatchEvent(
    new CustomEvent<ChatIntent>(CHAT_INTENT_EVENT, { detail: intent }),
  )
}

export function consumePendingChatIntent() {
  const intent = pendingIntent
  pendingIntent = null
  return intent
}

export function askChatQuestion(question: string) {
  dispatchChatIntent({ mode: 'send', text: question })
}

export function insertChatDraft(text: string) {
  dispatchChatIntent({ mode: 'draft', text })
}

function toBlockQuote(text: string): string {
  return text
    .trim()
    .split('\n')
    .map(line => `> ${line}`)
    .join('\n')
}

export function buildQuotedChatDraft({
  roleId,
  prompt,
  quote,
}: {
  roleId: string
  prompt: string
  quote: string
}) {
  const normalizedPrompt = prompt.trim()
  const normalizedQuote = quote.trim()

  if (!normalizedQuote) {
    return `@${roleId} ${normalizedPrompt}`
  }

  return `@${roleId} ${normalizedPrompt}\n\n${toBlockQuote(normalizedQuote)}\n\n`
}
