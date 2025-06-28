<template>
  <div class="model-chat-container">
    <!-- 左侧边栏：会话列表和操作 -->
    <div class="chat-sidebar">
      <div class="sidebar-header">
        <el-button
          type="primary"
          :icon="ChatDotRound"
          style="width: 100%"
          @click="createNewSession"
          >新对话</el-button
        >
      </div>
      <el-scrollbar class="session-list">
        <div
          v-for="session in chatSessions"
          :key="session.id"
          class="session-item"
          :class="{ active: currentSession?.id === session.id }"
          @click="selectSession(session)"
        >
          <div class="session-title">{{ session.title }}</div>
          <div class="session-info">
            <span>{{ formatTime(session.created_at) }}</span>
            <el-tooltip content="删除对话" placement="top">
              <el-icon @click.stop="deleteSession(session.id)"><Delete /></el-icon>
            </el-tooltip>
          </div>
        </div>
        <el-empty v-if="!chatSessions.length" description="暂无对话" :image-size="60" />
      </el-scrollbar>
    </div>

    <!-- 右侧主区域：聊天界面 -->
    <div class="chat-main">
      <div v-if="currentSession" class="chat-content">
        <!-- 聊天区域头部 -->
        <div class="chat-header">
          <div class="header-title">{{ currentSession.title }}</div>
        </div>

        <!-- 消息列表 -->
        <el-scrollbar ref="messageList" class="message-list">
          <div v-for="message in currentSession.messages" :key="message.id" class="message-item" :class="message.role">
            <el-avatar class="message-avatar" :src="message.role === 'user' ? userAvatar : '/logo.png'" size="default" />
            <div class="message-content-wrapper">
              <div class="message-info">
                <strong>{{ message.role === 'user' ? userName : 'AI' }}</strong>
                <span class="message-time">{{ formatTime(message.created_at) }}</span>
              </div>
              <div class="message-text" v-html="renderMarkdown(message.content)"></div>
            </div>
          </div>
        </el-scrollbar>

        <!-- 输入区域 -->
        <div class="chat-input-area">
          <!-- 输入框上方的控制栏 -->
          <div class="input-controls">
            <div class="model-selector">
              <span class="control-label">对话模型:</span>
              <el-select
                v-model="selectedModel"
                placeholder="请选择模型"
                size="default"
                class="model-select"
                :disabled="sending"
              >
                <el-option
                  v-for="model in availableModels"
                  :key="model.name"
                  :label="model.name"
                  :value="model.name"
                />
              </el-select>
            </div>
            <div class="prompt-selector">
              <span class="control-label">提示词:</span>
              <el-select
                v-model="selectedPrompt"
                placeholder="请选择提示词"
                size="default"
                class="prompt-select"
                :disabled="sending"
                clearable
              >
                <el-option
                  v-for="prompt in availablePrompts"
                  :key="prompt.id"
                  :label="prompt.name"
                  :value="prompt.id"
                />
              </el-select>
            </div>
            <div class="streaming-option">
              <span class="control-label">流式输出:</span>
              <el-switch
                v-model="isStreaming"
                size="default"
                :disabled="sending"
                active-color="var(--primary-blue)"
                inactive-color="var(--medium-blue)"
              />
            </div>
          </div>
          
          <!-- 输入框 -->
          <el-input
            v-model="inputMessage"
            type="textarea"
            :rows="3"
            resize="none"
            placeholder="输入消息... (Shift + Enter 换行)"
            class="message-input"
            @keydown.enter.prevent="handleEnter"
          />
          
          <!-- 发送按钮 -->
          <div class="send-actions">
            <el-button 
              type="primary" 
              :loading="sending" 
              :disabled="!inputMessage.trim()" 
              @click="sendMessage"
              class="send-button"
            >
              发送
            </el-button>
          </div>
        </div>
      </div>
      <div v-else class="welcome-area">
         <el-icon size="80" color="#c0c4cc"><ChatDotRound /></el-icon>
        <h2>开始对话</h2>
        <p>从左侧选择一个对话或创建一个新对话</p>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted, nextTick } from 'vue'
import { useStore } from 'vuex'
import { ElMessageBox } from 'element-plus'
import { message } from '../utils/message'
import { ChatDotRound, Delete, Avatar, Reading } from '@element-plus/icons-vue'
import { chatAPI, modelAPI } from '../utils/api'
import { marked } from 'marked'
import hljs from 'highlight.js'

export default {
  name: 'ModelChat',
  components: {
    ChatDotRound,
    Delete,
    Avatar,
    Reading
  },
  setup() {
    const store = useStore()
    
    const chatSessions = ref([])
    const currentSession = ref(null)
    const availableModels = ref([])
    const availablePrompts = ref([])
    const selectedModel = ref('')
    const selectedPrompt = ref('')
    const inputMessage = ref('')
    const isStreaming = ref(true)
    const sending = ref(false)
    const messageList = ref(null)
    
    const userName = computed(() => store.getters.userName)
    const userAvatar = computed(() => {
      // 使用本地默认头像，避免外部服务不稳定的问题
      return `/imgs/default-avatar.svg`
    })
    
    const renderer = new marked.Renderer()
    renderer.code = (code, language) => {
      const validLanguage = hljs.getLanguage(language) ? language : 'plaintext'
      const highlightedCode = hljs.highlight(code, { language: validLanguage }).value
      return `<pre><code class="hljs ${validLanguage}">${highlightedCode}</code></pre>`
    }
    marked.setOptions({ renderer })
    
    const renderMarkdown = (content) => {
      return marked.parse(content || '')
    }
    
    const formatTime = (timeStr) => {
      if (!timeStr) return ''
      const date = new Date(timeStr)
      return date.toLocaleString('zh-CN', {
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      })
    }
    
    const scrollToBottom = () => {
      nextTick(() => {
        const scrollbar = messageList.value
        if (scrollbar && scrollbar.wrapRef) {
          scrollbar.setScrollTop(scrollbar.wrapRef.scrollHeight)
        }
      })
    }

    const loadModels = async () => {
      try {
        const response = await modelAPI.getModels()
        const models = Array.isArray(response.data) ? response.data : (Array.isArray(response) ? response : [])
        availableModels.value = models.filter(m => m.status === 'active')
        if (availableModels.value.length > 0 && !selectedModel.value) {
          selectedModel.value = availableModels.value[0].name
        }
      } catch (error) {
        console.error('加载模型列表失败:', error)
        // 如果加载失败，提供一些默认模型选项
        availableModels.value = [
          { name: 'qwen2-7b-instruct', status: 'active' },
          { name: 'chatglm3-6b', status: 'active' },
          { name: 'llama2-7b-chat', status: 'active' }
        ]
        if (!selectedModel.value) {
          selectedModel.value = availableModels.value[0].name
        }
      }
    }

    const loadPrompts = async () => {
      try {
        // TODO: 从API加载提示词列表
        // const prompts = await promptAPI.getPrompts()
        // availablePrompts.value = prompts
        availablePrompts.value = []
      } catch (error) {
        console.error('加载提示词失败:', error)
        availablePrompts.value = []
      }
    }

    const loadSessions = async () => {
      try {
        const response = await chatAPI.getSessions()
        const sessions = Array.isArray(response.data) ? response.data : (Array.isArray(response) ? response : [])
        chatSessions.value = sessions
        if (sessions.length > 0 && !currentSession.value) {
          selectSession(sessions[0])
        }
      } catch (error) {
        console.error('加载会话失败:', error)
        chatSessions.value = []
      }
    }
    
    const createNewSession = () => {
      currentSession.value = {
        id: null, // null id 代表这是一个尚未保存到后端的新会话
        title: '新对话',
        messages: [],
        created_at: new Date().toISOString()
      }
    }
    
    const selectSession = async (session) => {
      try {
        const sessionDetail = await chatAPI.getSession(session.id)
        currentSession.value = sessionDetail
        scrollToBottom()
      } catch (error) {
        console.error('加载会话详情失败:', error)
        message.error('加载会话详情失败')
      }
    }
    
    const deleteSession = async (sessionId) => {
      try {
        await ElMessageBox.confirm('这会永久删除此对话，确定吗？', '确认删除', {
          type: 'warning'
        })
        
        await chatAPI.deleteSession(sessionId)
        
        const index = chatSessions.value.findIndex(s => s.id === sessionId)
        if (index !== -1) {
          chatSessions.value.splice(index, 1)
        }
        
        if (currentSession.value?.id === sessionId) {
          currentSession.value = null
        }
        
        message.success('删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除会话失败:', error)
        }
      }
    }

    const handleEnter = (e) => {
      if (!e.shiftKey && !sending.value) {
        sendMessage()
      }
    }
    
    const sendMessage = async () => {
      if (!inputMessage.value.trim() || sending.value) return

      if (!selectedModel.value) {
        message.warning('请先选择一个对话模型')
        return
      }

      const userMessageContent = inputMessage.value.trim()
      inputMessage.value = ''
      sending.value = true
      let currentSessionId = currentSession.value.id

      // 立即在前端显示用户消息
      currentSession.value.messages.push({
        id: `user-${Date.now()}`,
        role: 'user',
        content: userMessageContent,
        created_at: new Date().toISOString()
      })
      scrollToBottom()

      try {
        // 准备发送数据
        const sendData = {
          session_id: currentSessionId,
          content: userMessageContent,
          model_name: selectedModel.value,
          is_streaming: isStreaming.value
        }
        
        // 如果选择了提示词，添加到请求中
        if (selectedPrompt.value) {
          const prompt = availablePrompts.value.find(p => p.id === selectedPrompt.value)
          if (prompt) {
            sendData.system_prompt = prompt.content
          }
        }
        
        // 如果是新会话 (id is null)，后端会自动创建
        const response = await chatAPI.sendMessage(sendData)
        
        // 如果是新创建的会话，需要刷新整个会话列表
        if (currentSessionId === null) {
          await loadSessions()
          // 找到新创建的会话并选中它
          const newSession = chatSessions.value.find(s => s.id === response.session_id)
          if (newSession) {
             currentSession.value = await chatAPI.getSession(newSession.id)
          }
        } else {
          // 否则，只更新消息列表
          const updatedSession = await chatAPI.getSession(currentSession.value.id)
          currentSession.value.messages = updatedSession.messages
        }

      } catch (error) {
        currentSession.value.messages.push({
          id: `error-${Date.now()}`,
          role: 'ai',
          content: '抱歉，请求出错，请稍后重试。',
          created_at: new Date().toISOString()
        })
      } finally {
        sending.value = false
        scrollToBottom()
      }
    }
    
    onMounted(() => {
      loadModels()
      loadPrompts()
      loadSessions()
    })
    
    return {
      chatSessions,
      currentSession,
      availableModels,
      availablePrompts,
      selectedModel,
      selectedPrompt,
      inputMessage,
      isStreaming,
      sending,
      messageList,
      userName,
      userAvatar,
      formatTime,
      renderMarkdown,
      handleEnter,
      createNewSession,
      selectSession,
      deleteSession,
      sendMessage,
      ChatDotRound,
      Delete,
      Reading
    }
  }
}
</script>

<style scoped>
@import 'highlight.js/styles/atom-one-dark.css';

/* 聊天容器 */
.model-chat-container {
  height: 100vh;
  display: flex;
  background: var(--background-blue);
  overflow: hidden;
}

/* 左侧边栏 */
.chat-sidebar {
  width: 350px;
  background: var(--bg-color);
  border-right: 2px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 1.5rem;
  border-bottom: 2px solid var(--border-color);
  background: var(--bg-color);
}

.sidebar-header .el-button {
  height: 56px;
  font-size: 1.3rem;
  font-weight: 600;
  border-radius: 12px;
}

/* 会话列表 */
.session-list {
  flex: 1;
  padding: 1rem;
}

.session-item {
  padding: 1.5rem;
  margin-bottom: 1rem;
  border-radius: 12px;
  background: var(--bg-color);
  border: 2px solid var(--border-color);
  cursor: pointer;
  transition: all 0.3s ease;
}

.session-item:hover {
  background: var(--light-blue);
  border-color: var(--medium-blue);
  transform: translateX(4px);
}

.session-item.active {
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
  border-color: var(--dark-blue);
  color: white;
  box-shadow: 0 4px 12px rgba(100, 168, 219, 0.3);
}

.session-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 0.5rem;
  color: inherit;
}

.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 1rem;
  color: inherit;
  opacity: 0.8;
}

.session-info .el-icon {
  cursor: pointer;
  padding: 0.3rem;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.session-info .el-icon:hover {
  background: rgba(255, 255, 255, 0.2);
}

/* 主聊天区域 */
.chat-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: var(--background-blue);
  overflow: hidden;
}

.chat-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

/* 聊天头部 */
.chat-header {
  padding: 1.5rem 2rem;
  background: var(--bg-color);
  border-bottom: 2px solid var(--border-color);
}

.header-title {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--text-color);
}

/* 消息列表 */
.message-list {
  flex: 1;
  padding: 1rem 2rem;
  background: var(--background-blue);
}

.message-item {
  display: flex;
  margin-bottom: 2rem;
  gap: 1rem;
}

.message-item.user {
  justify-content: flex-end;
}

.message-item.user .message-content-wrapper {
  order: -1;
  text-align: right;
}

.message-avatar {
  flex-shrink: 0;
  border: 2px solid var(--border-color);
}

.message-content-wrapper {
  max-width: 70%;
  background: var(--bg-color);
  border: 2px solid var(--border-color);
  border-radius: 16px;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.message-item.user .message-content-wrapper {
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
  color: white;
  border-color: var(--dark-blue);
}

.message-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.8rem;
  font-size: 1rem;
  opacity: 0.8;
}

.message-text {
  font-size: 1.2rem;
  line-height: 1.6;
  color: inherit;
}

/* 欢迎区域 */
.welcome-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  gap: 1.5rem;
  color: var(--text-color);
}

.welcome-area h2 {
  font-size: 2rem;
  font-weight: 600;
  margin: 0;
  color: var(--text-color);
}

.welcome-area p {
  font-size: 1.3rem;
  opacity: 0.7;
  margin: 0;
  color: var(--text-color);
}

/* 输入区域 */
.chat-input-area {
  padding: 2rem;
  background: var(--bg-color);
  border-top: 2px solid var(--border-color);
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 输入控制栏 */
.input-controls {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  gap: 2rem;
}

.model-selector,
.prompt-selector {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.streaming-option {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-left: auto;
}

.control-label {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
  white-space: nowrap;
}

.model-select,
.prompt-select {
  width: 200px;
}

/* 发送按钮区域 */
.send-actions {
  display: flex;
  justify-content: flex-end;
}

.send-button {
  width: 160px;
  height: 56px;
  font-size: 1.3rem;
  font-weight: 600;
  border-radius: 16px;
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
  border: none;
  box-shadow: 0 4px 12px rgba(100, 168, 219, 0.3);
  transition: all 0.3s ease;
}

.send-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(100, 168, 219, 0.4);
}

/* 代码高亮样式调整 */
.message-text :deep(pre) {
  background: var(--el-color-info-light-9) !important;
  padding: 1.5rem !important;
  border-radius: 12px !important;
  font-size: 1.1rem !important;
  margin: 1rem 0 !important;
  border: 1px solid var(--el-border-color) !important;
}

.message-text :deep(code) {
  background: var(--el-color-info-light-9) !important;
  padding: 0.3rem 0.6rem !important;
  border-radius: 6px !important;
  font-size: 1.1rem !important;
  color: var(--el-text-color-primary) !important;
  border: 1px solid var(--el-border-color) !important;
}

.message-text :deep(blockquote) {
  border-left: 4px solid var(--el-color-primary) !important;
  padding-left: 1.5rem !important;
  background: var(--el-color-primary-light-9) !important;
  margin: 1rem 0 !important;
  border-radius: 0 12px 12px 0 !important;
  color: var(--el-text-color-primary) !important;
}
</style> 