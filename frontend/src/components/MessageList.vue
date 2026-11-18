<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { Message } from '../types'
const props = defineProps<{ messages: Message[] }>()
const container = ref<HTMLElement | null>(null)
watch(() => props.messages, async () => {
  await nextTick()
  container.value?.scrollTo({ top: container.value.scrollHeight, behavior: 'smooth' })
})
</script>

<template>
  <div ref="container" class="messages" role="log" aria-label="聊天记录" aria-live="polite">
    <div v-if="!messages.length" class="empty"><h2>从一句话开始</h2><p>输入一条虚构消息，检查聊天和历史记录是否正常。</p></div>
    <article v-for="message in messages" :key="message.id" class="message" :class="message.role">
      <strong>{{ message.role === 'user' ? '你' : 'Luna · 模拟' }}</strong>
      <p>{{ message.content }}</p>
    </article>
  </div>
</template>
