<script setup>
import { ref, nextTick, computed } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { sendChatMessage } from '@/api/index'

const props = defineProps({ auditId: { type: String, required: true } })

const open      = ref(false)
const loading   = ref(false)
const input     = ref('')
const messages  = ref([])
const messagesEl = ref(null)

const history = computed(() =>
  messages.value.map(m => ({ role: m.role, content: m.content }))
)

async function send() {
  const q = input.value.trim()
  if (!q || loading.value) return

  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true
  await scrollBottom()

  try {
    const data = await sendChatMessage(props.auditId, q, history.value.slice(0, -1))
    messages.value.push({ role: 'assistant', content: data.answer ?? data?.data?.answer ?? '' })
  } catch {
    messages.value.push({ role: 'assistant', content: 'Error al conectar con el asistente. Intenta de nuevo.' })
  } finally {
    loading.value = false
    await scrollBottom()
  }
}

function onKeydown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

async function scrollBottom() {
  await nextTick()
  if (messagesEl.value) messagesEl.value.scrollTop = messagesEl.value.scrollHeight
}

function toggle() {
  open.value = !open.value
  if (open.value && messages.value.length === 0) {
    messages.value.push({
      role: 'assistant',
      content: '¡Hola! Soy tu asistente de auditoría. Puedo responder preguntas sobre los documentos cargados. ¿En qué te ayudo?',
    })
  }
}
</script>

<template>
  <div class="chatbot-root">
    <!-- Panel -->
    <Transition name="chat-slide">
      <div v-if="open" class="chatbot-panel">
        <div class="chatbot-header">
          <div style="display:flex;align-items:center;gap:8px;">
            <AppIcon name="cpu" :size="14" style="color:var(--accent)" />
            <span style="font-size:13px;font-weight:600;">Asistente COSFI</span>
          </div>
          <button class="btn btn-ghost btn-icon btn-sm" @click="open = false">
            <AppIcon name="x" :size="13" />
          </button>
        </div>

        <div ref="messagesEl" class="chatbot-messages">
          <div
            v-for="(msg, i) in messages"
            :key="i"
            class="chatbot-msg"
            :class="msg.role === 'user' ? 'chatbot-msg-user' : 'chatbot-msg-ai'"
          >
            <div v-if="msg.role === 'assistant'" class="chatbot-avatar">
              <AppIcon name="cpu" :size="11" style="color:var(--accent)" />
            </div>
            <div class="chatbot-bubble">{{ msg.content }}</div>
          </div>

          <div v-if="loading" class="chatbot-msg chatbot-msg-ai">
            <div class="chatbot-avatar">
              <AppIcon name="cpu" :size="11" style="color:var(--accent)" />
            </div>
            <div class="chatbot-bubble chatbot-typing">
              <span /><span /><span />
            </div>
          </div>
        </div>

        <div class="chatbot-input-row">
          <textarea
            v-model="input"
            class="chatbot-input"
            placeholder="Escribe tu pregunta…"
            rows="1"
            @keydown="onKeydown"
          />
          <button
            class="btn btn-primary btn-icon btn-sm"
            :disabled="!input.trim() || loading"
            @click="send"
          >
            <AppIcon name="arrow-up" :size="13" />
          </button>
        </div>
      </div>
    </Transition>

    <!-- Botón flotante -->
    <div class="chatbot-fab-wrapper">
      <span class="chatbot-fab-label">{{ open ? '' : 'CHAT COSFI' }}</span>
      <button class="chatbot-fab" @click="toggle" :class="{ active: open }">
        <div v-if="!open" class="chatbot-fab-ping" />
        <AppIcon :name="open ? 'x' : 'cpu'" :size="18" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.chatbot-root {
  position: fixed;
  bottom: 24px;
  right: 24px;
  z-index: 1000;
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 12px;
}

.chatbot-fab-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.chatbot-fab-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.04em;
  color: var(--accent);
  opacity: 0.75;
  white-space: nowrap;
  pointer-events: none;
  transition: opacity 0.2s;
  font-family: 'JetBrains Mono', monospace;
}

.chatbot-fab {
  position: relative;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: var(--surface-2);
  color: var(--accent);
  border: 1px solid var(--border);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 0 1px rgba(34,211,238,0.15), 0 4px 20px rgba(0,0,0,0.5);
  transition: all 0.2s ease;
  outline: none;
}
.chatbot-fab:hover {
  border-color: var(--accent);
  box-shadow: 0 0 0 3px rgba(34,211,238,0.12), 0 0 18px rgba(34,211,238,0.25), 0 4px 20px rgba(0,0,0,0.5);
  transform: translateY(-2px);
  color: var(--accent);
}
.chatbot-fab.active {
  border-color: var(--border-2);
  color: var(--text-2);
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  transform: none;
}

.chatbot-fab-ping {
  position: absolute;
  inset: -3px;
  border-radius: 50%;
  border: 1px solid rgba(34,211,238,0.35);
  animation: fab-ping 2.5s ease-out infinite;
  pointer-events: none;
}
@keyframes fab-ping {
  0%   { transform: scale(1);    opacity: 0.6; }
  70%  { transform: scale(1.35); opacity: 0;   }
  100% { transform: scale(1.35); opacity: 0;   }
}

.chatbot-panel {
  width: 360px;
  height: 500px;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 12px;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  box-shadow: 0 8px 32px rgba(0,0,0,0.4);
}

.chatbot-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid var(--border);
  background: var(--surface-2);
}

.chatbot-messages {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chatbot-msg {
  display: flex;
  gap: 8px;
  align-items: flex-end;
}
.chatbot-msg-user { flex-direction: row-reverse; }

.chatbot-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  background: var(--accent-dim);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.chatbot-bubble {
  max-width: 78%;
  padding: 8px 11px;
  border-radius: 10px;
  font-size: 12.5px;
  line-height: 1.55;
  white-space: pre-wrap;
  word-break: break-word;
}
.chatbot-msg-ai .chatbot-bubble {
  background: var(--surface-2);
  border: 1px solid var(--border);
  color: var(--text);
  border-bottom-left-radius: 2px;
}
.chatbot-msg-user .chatbot-bubble {
  background: var(--accent);
  color: #000;
  font-weight: 500;
  border-bottom-right-radius: 2px;
}

.chatbot-typing {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 10px 14px;
}
.chatbot-typing span {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: var(--text-3);
  animation: bounce 1.2s infinite;
}
.chatbot-typing span:nth-child(2) { animation-delay: 0.2s; }
.chatbot-typing span:nth-child(3) { animation-delay: 0.4s; }
@keyframes bounce {
  0%, 60%, 100% { transform: translateY(0); }
  30% { transform: translateY(-5px); }
}

.chatbot-input-row {
  display: flex;
  gap: 8px;
  padding: 10px 12px;
  border-top: 1px solid var(--border);
  background: var(--surface-2);
}

.chatbot-input {
  flex: 1;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 8px;
  color: var(--text);
  font-size: 12.5px;
  padding: 7px 10px;
  resize: none;
  outline: none;
  font-family: inherit;
  line-height: 1.4;
  max-height: 80px;
  overflow-y: auto;
}
.chatbot-input:focus { border-color: var(--accent); }

/* Slide transition */
.chat-slide-enter-active, .chat-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.chat-slide-enter-from, .chat-slide-leave-to {
  opacity: 0;
  transform: translateY(12px) scale(0.97);
}
</style>
