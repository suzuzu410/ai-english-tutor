<template>
  <div class="flex flex-col h-screen bg-gray-50 text-gray-800 font-sans">
    <!-- 顶部导航 -->
    <header class="bg-white shadow-sm p-4 text-center font-bold text-xl text-blue-600">
      LinguaAgent - AI 英语私教
    </header>

    <!-- 聊天区域 -->
    <main class="flex-1 overflow-y-auto p-4 space-y-6" ref="chatContainer">
      <div v-for="(msg, index) in messages" :key="index"
           :class="['flex', msg.role === 'user' ? 'justify-end' : 'justify-start']">

        <!-- AI 消息 -->
        <div v-if="msg.role === 'assistant'" class="max-w-[80%] bg-white p-4 rounded-2xl rounded-tl-none shadow-sm border border-gray-100">
          <!-- 占位符状态显示 -->
          <div v-if="msg.content === LOADING_TEXT" class="text-gray-400 flex items-center gap-2">
            <svg class="animate-spin h-4 w-4 text-blue-500" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
              <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
              <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
            </svg>
            {{ msg.content }}
          </div>
          <div v-else class="prose prose-sm max-w-none text-gray-700" v-html="renderMarkdown(msg.content)"></div>
        </div>

        <!-- 用户消息 -->
        <div v-else class="max-w-[80%] bg-blue-500 text-white p-4 rounded-2xl rounded-tr-none shadow-sm">
          {{ msg.content }}
        </div>
      </div>

      <!-- 🚀 新增：工具调用状态提示（显示在聊天列表底部） -->
      <div v-if="toolStatus" class="flex justify-start">
        <div class="bg-blue-50 text-blue-600 text-sm px-4 py-2 rounded-full border border-blue-100 flex items-center gap-2 shadow-sm animate-pulse">
          <span>🛠️</span> {{ toolStatus }}
        </div>
      </div>
    </main>

    <!-- 输入区域 -->
    <footer class="bg-white border-t border-gray-200 p-4">
      <div class="max-w-4xl mx-auto flex gap-3">
        <input v-model="inputMessage" @keyup.enter="sendMessage" type="text"
               placeholder="输入你想问的问题... (例如: What does 'resilient' mean?)"
               class="flex-1 border border-gray-300 rounded-full px-5 py-3 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all" />
        <button @click="sendMessage" :disabled="isLoading || !inputMessage.trim()"
                class="bg-blue-500 hover:bg-blue-600 disabled:bg-gray-300 text-white px-6 py-3 rounded-full font-medium transition-colors">
          发送
        </button>
      </div>
    </footer>
  </div>
</template>

<script setup>
import { ref, nextTick } from 'vue'
import { marked } from 'marked'
import { fetchEventSource } from '@microsoft/fetch-event-source'

const LOADING_TEXT = '正在检索知识库并思考...'

const messages = ref([
  { role: 'assistant', content: 'Hello! I am your AI English tutor. How can I help you today?' }
])
const inputMessage = ref('')
const isLoading = ref(false)
const chatContainer = ref(null)
const userId = 'student_01' // 暂时写死
const toolStatus = ref('') // 🚀 新增：用于存放工具状态

// Markdown 渲染
const renderMarkdown = (text) => {
  return marked.parse(text || '')
}

// 自动滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

const sendMessage = async () => {
  if (!inputMessage.value.trim() || isLoading.value) return

  const userText = inputMessage.value
  inputMessage.value = ''
  toolStatus.value = '' // 重置工具状态

  // 添加用户消息和空的 AI 消息
  messages.value.push({ role: 'user', content: userText })
  messages.value.push({ role: 'assistant', content: LOADING_TEXT })
  isLoading.value = true
  scrollToBottom()

  try {
    await fetchEventSource('http://127.0.0.1:8000/api/chat', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: userId, message: userText }),

      onmessage(ev) {
        const lastMsg = messages.value[messages.value.length - 1]

        // 1. 结束标志
        if (ev.data === '[DONE]') {
          isLoading.value = false
          toolStatus.value = ''
          return
        }

        // 2. 错误信息
        if (ev.data.startsWith('[Error]')) {
          lastMsg.content = `抱歉，系统出错：${ev.data}`
          isLoading.value = false
          toolStatus.value = ''
          return
        }

        // 🚀 3. 核心新增：拦截工具调用状态
        if (ev.data.startsWith('[STATUS]')) {
          toolStatus.value = ev.data.replace('[STATUS]', '').trim()
          return
        }

        // 4. 收到真实数据前，清除工具状态标签
        toolStatus.value = ''

        // 5. 拼接流式内容
        if (lastMsg.content === LOADING_TEXT) {
          lastMsg.content = ev.data
        } else {
          lastMsg.content += ev.data
        }

        scrollToBottom()
      },

      onerror(err) {
        console.error('SSE Error:', err)
        isLoading.value = false
        toolStatus.value = ''
        const lastMsg = messages.value[messages.value.length - 1]
        if (lastMsg && lastMsg.content === LOADING_TEXT) {
          lastMsg.content = '网络连接失败，请检查后端是否启动。'
        }
        throw err // 阻止自动重连
      }
    })
  } catch (error) {
    isLoading.value = false
    toolStatus.value = ''
    const lastMsg = messages.value[messages.value.length - 1]
    if (lastMsg && lastMsg.content === LOADING_TEXT) {
      lastMsg.content = '网络连接失败，请检查后端是否启动。'
    }
  }
}
</script>