import type { ApiError } from '../types'

export const API_BASE = import.meta.env.VITE_API_BASE ?? ''

export class ApiRequestError extends Error {
  hint?: string

  constructor(message: string, hint?: string) {
    super(message)
    this.name = 'ApiRequestError'
    this.hint = hint
  }
}

async function fetchResponse(path: string, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(`${API_BASE}${path}`, init)
  } catch (error) {
    if (error instanceof TypeError) {
      throw new ApiRequestError(
        `Cannot reach API at ${API_BASE}. Start the backend with: PYTHONPATH=src python -m cine_forge.api`
      )
    }
    throw error
  }
}

async function readErrorPayload(response: Response): Promise<ApiError | null> {
  try {
    return (await response.json()) as ApiError
  } catch {
    return null
  }
}

async function throwRequestError(response: Response, fallbackMessage: string): Promise<never> {
  const payload = await readErrorPayload(response)
  const message = payload?.message ?? fallbackMessage
  throw new ApiRequestError(message, payload?.hint ?? undefined)
}

export async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetchResponse(path, {
    headers: { 'Content-Type': 'application/json' },
    ...init,
  })

  if (!response.ok) {
    await throwRequestError(response, `Request failed (${response.status})`)
  }

  return (await response.json()) as T
}

export async function requestText(path: string, init?: RequestInit): Promise<string> {
  const response = await fetchResponse(path, init)
  if (!response.ok) {
    throw new ApiRequestError(`Request failed (${response.status})`)
  }
  return response.text()
}

export async function requestFormData<T>(
  path: string,
  form: FormData,
  init?: Omit<RequestInit, 'body'>,
): Promise<T> {
  const response = await fetchResponse(path, {
    ...init,
    body: form,
  })

  if (!response.ok) {
    await throwRequestError(response, `Request failed (${response.status})`)
  }

  return (await response.json()) as T
}
