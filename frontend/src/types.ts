/** Public API contract; keep aligned with backend/app/schemas.py. */
export interface Conversation { id: string; title: string; created_at: string }
export interface Message {
  id: string
  role: 'user' | 'assistant'
  content: string
  created_at: string
}
export interface Reply { message: Message; sources: string[]; provider: 'mock' }
export interface PendingMessage { text: string; requestId: string }
