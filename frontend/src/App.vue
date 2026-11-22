<script setup lang="ts">
import { onMounted } from 'vue'
import MessageList from './components/MessageList.vue'
import { useChat } from './composables/useChat'
const chat = useChat()
const { conversations, selectedId, mode, messages, draft, busy, error, pending, canSend } = chat
onMounted(chat.initialize)
</script>

<template>
  <div class="shell">
    <aside>
      <div class="brand">Luna Heart<span>开发工作台</span></div>
      <button class="primary" :disabled="busy || !!pending" @click="chat.create">＋ 新建会话</button>
      <nav aria-label="历史会话">
        <button v-for="item in conversations" :key="item.id" class="conversation"
          :class="{ active: selectedId === item.id }" :disabled="busy || !!pending" @click="chat.select(item.id)">
          {{ item.title }}
        </button>
      </nav>
      <p class="sidebar-note">本地单用户版本<br />日记、状态与知识库将分阶段接入。</p>
    </aside>
    <main>
      <header><div><h1>与 Luna 聊天</h1><p>会话保存在本机，支持多轮上下文。</p></div><span v-if="mode" class="badge">{{ mode === 'cloud_api' ? 'DeepSeek API' : 'Mock 模式' }}</span></header>
      <p v-if="mode === 'cloud_api'" class="notice">发送时，当前消息和本会话的近期对话会发给 DeepSeek。请使用虚构信息。</p>
      <p v-else-if="mode === 'local_mock'" class="notice">当前为固定模拟回复，仅用于开发，请使用虚构信息。</p>
      <MessageList :messages="messages" />
      <div v-if="error" class="error" role="alert">
        {{ error }}
        <template v-if="pending"><button :disabled="busy" @click="chat.submit(true)">重试原消息</button><button :disabled="busy" @click="chat.discardPending">取消重试</button></template>
        <button v-else-if="!selectedId" :disabled="busy" @click="chat.initialize">重新连接</button>
      </div>
      <form class="composer" @submit.prevent="chat.submit()">
        <label for="message">消息</label>
        <textarea id="message" v-model="draft" maxlength="4000" rows="3" :disabled="busy || !!pending || !selectedId" placeholder="输入虚构的测试消息…" />
        <div class="composer-footer"><span>{{ draft.length }} / 4000 · 当前仅开发演示</span><button class="primary" type="submit" :disabled="!canSend">{{ busy ? '处理中…' : '发送消息' }}</button></div>
      </form>
    </main>
  </div>
</template>
