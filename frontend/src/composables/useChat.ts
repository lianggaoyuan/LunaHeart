import { computed, ref } from 'vue'
import { chatApi } from '../api'
import type { Conversation, Message, PendingMessage } from '../types'

/** Session state and request lifecycle; components only render and emit actions. */
export function useChat() {
  const conversations = ref<Conversation[]>([])
  const selectedId = ref<string | null>(null)
  const messages = ref<Message[]>([])
  const draft = ref('')
  const busy = ref(false)
  const error = ref('')
  const pending = ref<PendingMessage | null>(null)
  const canSend = computed(() => !busy.value && !!selectedId.value && !!draft.value.trim() && !pending.value)

  async function run(action: () => Promise<void>) {
    if (busy.value) return
    busy.value = true
    error.value = ''
    try { await action() }
    catch (cause) { error.value = cause instanceof Error ? cause.message : '请求失败，请重试' }
    finally { busy.value = false }
  }

  async function initialize() {
    await run(async () => {
      conversations.value = await chatApi.list()
      const current = conversations.value[0] ?? await chatApi.create()
      if (!conversations.value.length) conversations.value = [current]
      const history = await chatApi.history(current.id)
      selectedId.value = current.id
      messages.value = history
    })
  }

  async function select(id: string) {
    if (pending.value) return
    await run(async () => {
      const history = await chatApi.history(id)
      selectedId.value = id
      messages.value = history
      draft.value = ''
    })
  }

  async function create() {
    if (pending.value) return
    await run(async () => {
      const conversation = await chatApi.create()
      conversations.value.unshift(conversation)
      selectedId.value = conversation.id
      messages.value = []
      draft.value = ''
    })
  }

  async function submit(retry = false) {
    if (!selectedId.value || busy.value) return
    if (!retry && !canSend.value) return
    const attempt = retry ? pending.value : { text: draft.value.trim(), requestId: crypto.randomUUID() }
    if (!attempt) return
    await run(async () => {
      pending.value = attempt
      const conversationId = selectedId.value!
      await chatApi.send(conversationId, attempt)
      // Fetch canonical history: retry may refer to an exchange already committed.
      messages.value = await chatApi.history(conversationId)
      pending.value = null
      draft.value = ''
      // A list refresh failing must not restore an already completed pending send.
      conversations.value = await chatApi.list()
    })
  }

  function discardPending() {
    pending.value = null
    error.value = '已取消本地重试；服务器可能已保存消息，请重新选择会话核对记录。'
  }

  return { conversations, selectedId, messages, draft, busy, error, pending, canSend,
    initialize, select, create, submit, discardPending }
}
