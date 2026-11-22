import type { Conversation, Health, Message, PendingMessage, Reply } from './types'

const base = import.meta.env.VITE_API_BASE_URL ?? '/api/v1'

async function responseError(response: Response): Promise<Error> {
  const body = await response.json().catch(() => null)
  return new Error(body?.error?.message ?? `请求失败 (${response.status})`)
}

async function request<T>(path: string, options: RequestInit = {}, timeout = 30_000): Promise<T> {
  const controller = new AbortController()
  const timer = setTimeout(() => controller.abort(), timeout)
  try {
    const response = await fetch(`${base}${path}`, {
      ...options, signal: controller.signal,
      headers: { 'Content-Type': 'application/json', ...options.headers },
    })
    if (!response.ok) throw await responseError(response)
    return await response.json() as T
  } catch (error) {
    if (controller.signal.aborted) throw new Error('请求超时，可使用原消息重试')
    throw error
  } finally { clearTimeout(timer) }
}

export const chatApi = {
  health: () => request<Health>('/health'),
  list: () => request<Conversation[]>('/conversations'),
  create: () => request<Conversation>('/conversations', { method: 'POST' }),
  history: (id: string) => request<Message[]>(`/conversations/${id}/messages`),
  send: (id: string, message: PendingMessage) => request<Reply>(`/conversations/${id}/messages`, {
    method: 'POST', body: JSON.stringify({ message: message.text, client_message_id: message.requestId }),
  }, 90_000),
}
