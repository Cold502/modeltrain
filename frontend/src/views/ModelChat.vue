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
        >新对话
        </el-button
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
              <el-icon class="delete-icon" @click.stop="deleteSession(session.id)">
                <Delete/>
              </el-icon>
            </el-tooltip>
          </div>
        </div>
        <el-empty v-if="!chatSessions.length" description="暂无对话" :image-size="60"/>
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
            <el-avatar class="message-avatar" :src="message.role === 'user' ? userAvatar : '/logo.png'" size="default"/>
            <div class="message-content-wrapper">
              <div class="message-info">
                <strong>{{ message.role === 'user' ? userName : 'AI' }}</strong>
                <span class="message-time">{{ formatTime(message.created_at) }}</span>
                <span v-if="message.isStreaming" class="streaming-indicator">
                  <el-icon class="rotating"><Reading/></el-icon>
                  正在输出...
                </span>

              </div>

              <!-- 思维链显示 -->
              <div v-if="message.thinking && message.thinking.trim()" class="thinking-section">
                <div class="thinking-header" @click="toggleThinking(message)">
                  <el-icon>
                    <Reading/>
                  </el-icon>
                  <span>思维过程</span>
                  <el-icon class="collapse-icon" :class="{ rotated: message.showThinking }">
                    <ArrowDown/>
                  </el-icon>
                </div>
                <div v-show="message.showThinking" class="thinking-content">
                  <div class="thinking-text" v-html="renderMarkdown(message.thinking)"></div>
                </div>
              </div>

              <!-- 消息内容 -->
              <div class="message-text"
                   :class="{ 
                     'streaming-empty': message.isStreaming && !message.content.trim(),
                     'is-error': message.isError
                   }"
                   v-html="renderMarkdown(message.content) || (message.isStreaming ? '<span class=&quot;streaming-placeholder&quot;>AI正在思考中...</span>' : '')">
              </div>

              <!-- AI消息操作按钮 -->
              <div v-if="message.role === 'assistant' && !message.isStreaming" class="message-download-area">
                <!-- 错误消息的重新发送按钮 -->
                <el-button
                    v-if="message.isError"
                    type="warning"
                    size="small"
                    :icon="Refresh"
                    @click="retryMessage(message)"
                    class="retry-message-btn"
                >
                  重新发送
                </el-button>
                <!-- 正常消息的下载按钮 -->
                <el-button
                    v-else
                    type="primary"
                    size="small"
                    :icon="Download"
                    @click="downloadMessage(message)"
                    class="download-message-btn"
                >
                  下载
                </el-button>
              </div>
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
                    :key="model.configId"
                    :label="model.name"
                    :value="model.configId"
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
        <el-icon size="80" color="#c0c4cc">
          <ChatDotRound/>
        </el-icon>
        <h2>开始对话</h2>
        <p>从左侧选择一个对话或创建一个新对话</p>
      </div>
    </div>
  </div>
</template>

<script>
import {ref, computed, onMounted, nextTick, watch} from 'vue'
import {useStore} from 'vuex'
import {ElMessageBox, ElMessage} from 'element-plus'
import {message} from '../utils/message'
import {ChatDotRound, Delete, Avatar, Reading, ArrowDown, Download, Refresh} from '@element-plus/icons-vue'
import {chatAPI, modelAPI, modelConfigAPI} from '../utils/api'
import {marked} from 'marked'
import hljs from 'highlight.js'
import api from '../utils/api'
import { createSSEStream } from '../utils/tokenManager'
import { parseThinkingContent, enrichMessageWithThinking } from '../utils/thinkParser'
export default {
  name: 'ModelChat',
  components: {
    ChatDotRound,
    Delete,
    Avatar,
    Reading,
    ArrowDown,
    Download
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

    // 跟踪正在进行的流式响应
    const activeStreamingMessages = new Map() // sessionId -> { messageId, content, isStreaming }

    const userName = computed(() => store.getters.userName)
    const userAvatar = computed(() => {
      // 使用本地默认头像，避免外部服务不稳定的问题
      return `/imgs/default-avatar.svg`
    })

    const renderer = new marked.Renderer()
    renderer.code = (code, language) => {
      const validLanguage = hljs.getLanguage(language) ? language : 'plaintext'
      const highlightedCode = hljs.highlight(code, {language: validLanguage}).value
      return `<pre><code class="hljs ${validLanguage}">${highlightedCode}</code></pre>`
    }
    marked.setOptions({renderer})

    const renderMarkdown = (content) => {
      if (!content) return ''

      // 先处理转义符和换行
      let processedContent = content
          .replace(/\\n/g, '\n')           // 处理转义的换行符
          .replace(/\\t/g, '\t')           // 处理转义的制表符
          .replace(/\\r/g, '\r')           // 处理转义的回车符
          .replace(/\\\\/g, '\\')          // 处理转义的反斜杠
          .replace(/\\"/g, '"')            // 处理转义的双引号
          .replace(/\\'/g, "'")            // 处理转义的单引号

      // 将单个换行符转换为两个换行符，这样markdown会识别为段落分隔
      // 但是先保护已经是段落分隔的地方（连续两个或以上换行符）
      processedContent = processedContent
          .replace(/\n{2,}/g, '|||PARAGRAPH|||')  // 临时标记段落分隔
          .replace(/\n/g, '  \n')                 // 单个换行符前加两个空格（markdown换行语法）
          .replace(/\|\|\|PARAGRAPH\|\|\|/g, '\n\n') // 恢复段落分隔

      // 使用marked解析markdown
      return marked.parse(processedContent)
    }

    const formatTime = (timeStr) => {
      if (!timeStr) return ''
      const date = new Date(timeStr)

      // 检查是否是有效日期
      if (isNaN(date.getTime())) return ''

      // 直接显示时间，不做复杂判断
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
        const response = await modelConfigAPI.getModels()
        const models = Array.isArray(response.data) ? response.data : (Array.isArray(response) ? response : [])
        const filteredModels = models.filter(m => m.status === 1)
        
        availableModels.value = filteredModels.map(config => ({
          id: config.id,
          name: `${config.providerName}: ${config.modelName}`,
          providerName: config.providerName,
          modelName: config.modelName,
          configId: config.id
        }))
        
        if (availableModels.value.length > 0 && !selectedModel.value) {
          selectedModel.value = availableModels.value[0].configId
        }
        
        await nextTick()
      } catch (error) {
        console.error('加载模型列表失败:', error)
        availableModels.value = []
      }
    }

    const loadPrompts = async () => {
      try {
        const response = await chatAPI.getSystemPrompts()
        const prompts = Array.isArray(response.data) ? response.data : (Array.isArray(response) ? response : [])
        availablePrompts.value = prompts

        // 设置默认提示词
        const defaultPrompt = prompts.find(p => p.is_default)
        if (defaultPrompt && !selectedPrompt.value) {
          selectedPrompt.value = defaultPrompt.id
        }
      } catch (error) {
        console.error('加载提示词失败:', error)
        ElMessage.warning('加载系统提示词失败，请检查网络连接')
        availablePrompts.value = []
      }
    }

    const loadSessions = async () => {
      try {
        const response = await chatAPI.getSessions()
        const sessions = Array.isArray(response.data) ? response.data : (Array.isArray(response) ? response : [])
        chatSessions.value = sessions
      } catch (error) {
        console.error('加载会话失败:', error)
        ElMessage.warning('加载聊天历史失败，请检查网络连接')
        chatSessions.value = []
      }
    }

    const createNewSession = () => {
      currentSession.value = {
        id: null, // null id 代表这是一个尚未保存到后端的新会话
        title: '新对话', // 初始标题，会在第一条消息发送后更新
        messages: [],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString()
      }
    }

    const selectSession = async (session) => {
      try {
    const response = await chatAPI.getSession(session.id)
        console.log('🔍 获取会话详情响应:', response)
        console.log('🔍 响应数据结构:', {
          hasData: !!response.data,
          dataType: typeof response.data,
          hasMessages: !!response.data?.messages,
          messagesType: typeof response.data?.messages,
          messagesLength: response.data?.messages?.length || 0
        })

        // 确保响应数据格式正确
        const sessionDetail = response.data || response
        if (!sessionDetail || !sessionDetail.id) {
          throw new Error('会话数据格式错误')
        }

        // 确保messages是数组
        if (!Array.isArray(sessionDetail.messages)) {
          console.log('⚠️ messages不是数组，当前值:', sessionDetail.messages)
          sessionDetail.messages = []
        } else {
          console.log('✅ messages是数组，长度:', sessionDetail.messages.length)
          console.log('📋 消息列表:', sessionDetail.messages)
        }

        // 为历史消息解析思维过程
        sessionDetail.messages = sessionDetail.messages.map(message => {
          return {
            ...message,
            isStreaming: false
          }
        });

        // 检查是否有正在进行的流式响应
        const streamingInfo = activeStreamingMessages.get(session.id);
        if (streamingInfo) {
          // 检查消息列表中是否已经有这条消息
          const existingIndex = sessionDetail.messages.findIndex(
            msg => msg.id === streamingInfo.messageId
          );
          if (existingIndex === -1) {
            // 如果消息不在列表中，添加它（保持流式状态）
            sessionDetail.messages.push(streamingInfo.message);
            console.log('🔄 恢复正在进行的流式响应:', streamingInfo.messageId);
          }
        }

        currentSession.value = sessionDetail

        // 等待下一个tick后滚动到底部
        await nextTick()
        scrollToBottom()
      } catch (error) {
        console.error('❌ 加载会话详情失败:', error)
        if (error.response) {
          console.error('错误响应状态:', error.response.status)
          console.error('错误响应数据:', error.response.data)
        }
        ElMessage.error('加载会话详情失败: ' + (error.response?.data?.detail || error.message))

        // 如果加载失败，创建一个空会话以避免界面错误
        currentSession.value = {
          id: session.id,
          title: session.title || '加载失败的会话',
          messages: [],
          created_at: session.created_at || new Date().toISOString(),
          updated_at: session.updated_at || new Date().toISOString()
        }
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

    const downloadMessage = async (message) => {
      try {
        if (message.role !== 'assistant') {
          ElMessage.warning('只能下载AI回答')
          return
        }

        // 格式化单条AI回答为文本
        let txtContent = `AI回答\n`
        txtContent += `回答时间: ${new Date(message.created_at).toLocaleString('zh-CN')}\n`
        txtContent += '='.repeat(50) + '\n\n'

        // 如果有思维过程，先显示思维过程
        if (message.thinking && message.thinking.trim()) {
          txtContent += `思维过程:\n${message.thinking.trim()}\n\n`
          txtContent += '-'.repeat(30) + '\n\n'
        }

        txtContent += `回答内容:\n${message.content}\n`

        // 创建下载
        const blob = new Blob([txtContent], {type: 'text/plain;charset=utf-8'})
        const url = window.URL.createObjectURL(blob)
        const link = document.createElement('a')
        link.href = url
        link.download = `AI回答_${new Date(message.created_at).toISOString().slice(0, 10)}_${Date.now()}.txt`
        document.body.appendChild(link)
        link.click()
        document.body.removeChild(link)
        window.URL.revokeObjectURL(url)

        ElMessage.success('AI回答已下载')
      } catch (error) {
        console.error('下载AI回答失败:', error)
        ElMessage.error('下载失败: ' + error.message)
      }
    }

    const retryMessage = async (message) => {
      try {
        // 找到对应的用户消息
        const messageIndex = currentSession.value.messages.findIndex(msg => msg.id === message.id);
        if (messageIndex === -1) {
          ElMessage.error('找不到对应的消息');
          return;
        }
        
        // 找到前一条用户消息
        let userMessage = null;
        for (let i = messageIndex - 1; i >= 0; i--) {
          if (currentSession.value.messages[i].role === 'user') {
            userMessage = currentSession.value.messages[i];
            break;
          }
        }
        
        if (!userMessage) {
          ElMessage.error('找不到对应的用户消息');
          return;
        }
        
        // 移除错误消息
        currentSession.value.messages.splice(messageIndex, 1);
        
        // 设置输入框内容为用户消息
        inputMessage.value = userMessage.content;
        
        // 重新发送消息
        await sendMessage();
        
        ElMessage.success('消息重新发送成功');
      } catch (error) {
        console.error('重新发送消息失败:', error);
        ElMessage.error('重新发送失败: ' + error.message);
      }
    }

    const handleEnter = (e) => {
      if (!e.shiftKey && !sending.value) {
        sendMessage()
      }
    }

    const toggleThinking = (message) => {
      message.showThinking = !message.showThinking
    }


    // 处理流式响应
const handleStreamingResponse = async (requestData, sessionId, onCompleteCallback) => {
  // 创建空的助手消息，使用时间戳+随机数确保唯一性
  const assistantMessageId = `assistant-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  const assistantMessage = {
    id: assistantMessageId,
    role: 'assistant',
    content: '',
    isStreaming: true,
    created_at: new Date().toISOString()
  };

  if (!currentSession.value.messages) {
    currentSession.value.messages = [];
  }
  currentSession.value.messages.push(assistantMessage);
  scrollToBottom();

  // 记录正在进行的流式响应
  activeStreamingMessages.set(sessionId, {
    messageId: assistantMessageId,
    message: assistantMessage
  });

  // 用于查找消息的辅助函数
  const findMessageById = (messages, id) => {
    return messages.findIndex(msg => msg.id === id);
  };

  try {
    // 使用新的SSE流式处理函数
    await createSSEStream(
      `${api.defaults.baseURL}/playground/chat/stream`,
      requestData,
      // onChunk回调：每次收到新内容时更新消息
      (currentContent) => {
        // 实时解析思维过程
        const parsed = parseThinkingContent(currentContent);
        const hasThinkStart = currentContent.includes('<think>');
        
        // 更新activeStreamingMessages中的内容
        const streamingInfo = activeStreamingMessages.get(sessionId);
        if (streamingInfo) {
          streamingInfo.message.content = parsed.content;
          streamingInfo.message.thinking = parsed.thinking;
          streamingInfo.message.showThinking = hasThinkStart;
        }
        
        // 只有当前显示的会话是原始会话时才更新UI
        if (currentSession.value.id === sessionId) {
          // 通过ID查找消息，而不是使用索引
          const messageIndex = findMessageById(currentSession.value.messages, assistantMessageId);
          if (messageIndex !== -1 && currentSession.value.messages[messageIndex]) {
            // 确保消息对象存在再更新
            const currentMessage = currentSession.value.messages[messageIndex];
            if (currentMessage) {
              currentSession.value.messages[messageIndex] = {
                ...currentMessage,
                content: parsed.content,
                thinking: parsed.thinking,
                showThinking: hasThinkStart, // 只要开始就显示，不等结束
                isStreaming: true
              };
              scrollToBottom();
            }
          }
        }
      },
      // onComplete回调：流式传输完成时
      (finalContent) => {
        // 清除流式状态记录
        activeStreamingMessages.delete(sessionId);
        
        // 只有当前显示的会话是原始会话时才更新UI
        if (currentSession.value.id === sessionId) {
          // 通过ID查找消息
          const messageIndex = findMessageById(currentSession.value.messages, assistantMessageId);
          if (messageIndex !== -1 && currentSession.value.messages[messageIndex]) {
            const currentMessage = currentSession.value.messages[messageIndex];
            if (currentMessage) {
              currentSession.value.messages[messageIndex] = { ...currentMessage, isStreaming: false };
              scrollToBottom();
            }
          }
        }
        // 通过回调将最终内容传递出去
        if (onCompleteCallback) {
          onCompleteCallback(finalContent);
        }
      },
      // onError回调：发生错误时
      (error) => {
        console.error('流式处理错误:', error);
        // 清除流式状态记录
        activeStreamingMessages.delete(sessionId);
        
        // 通过ID查找消息
        const messageIndex = findMessageById(currentSession.value.messages, assistantMessageId);
        if (messageIndex !== -1 && currentSession.value.messages[messageIndex]) {
          const currentMessage = currentSession.value.messages[messageIndex];
          if (currentMessage) {
            currentSession.value.messages[messageIndex] = {
              ...currentMessage,
              content: `错误: ${error.message}`,
              isStreaming: false
            };
          }
        }
        throw error;
      }
    );

  } catch (error) {
    console.error('流式请求处理失败:', error);
    // 清除流式状态记录
    activeStreamingMessages.delete(sessionId);

    // 移除正在流式传输的消息
    if (currentSession.value && currentSession.value.messages) {
      const messageIndex = currentSession.value.messages.findIndex(
        msg => msg.id === assistantMessage.id
      );
      if (messageIndex !== -1) {
        currentSession.value.messages.splice(messageIndex, 1);
      }
    }

    // 重新抛出错误以便上层处理
    throw error;
  }
};
const sendMessage = async () => {
  if (!inputMessage.value.trim() || sending.value) {
    return;
  }

  // 检查是否有正在进行的流式处理
  if (currentSession.value && currentSession.value.messages) {
    const lastMessage = currentSession.value.messages[currentSession.value.messages.length - 1];
    if (lastMessage && lastMessage.isStreaming) {
      ElMessage.warning('请等待当前回复完成');
      return;
    }
  }

  if (!selectedModel.value) {
    ElMessage.warning('请先选择一个对话模型');
    return;
  }

  const userMessageContent = inputMessage.value.trim();
  inputMessage.value = '';
  sending.value = true;



  // 立即在前端显示用户消息
  const userMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: userMessageContent,
    created_at: new Date().toISOString(),
    requestId: crypto.randomUUID ? crypto.randomUUID() : `req-${Date.now()}`
  };

  if (!currentSession.value.messages) {
    currentSession.value.messages = [];
  }
  currentSession.value.messages.push(userMessage);
  scrollToBottom();

  let originalSessionId = currentSession.value?.id || null;
  // 提前保存用户消息，确保不会因AI调用失败而丢失
  try {
    if (!originalSessionId) {
      // 如果是新会话，先创建会话并获取ID
      const title = userMessageContent.length > 20
        ? userMessageContent.substring(0, 20) + '...'
        : userMessageContent;
      const sessionResponse = await chatAPI.createSession({ title });
      originalSessionId = sessionResponse.data.id;
      currentSession.value.id = originalSessionId; // 更新当前会话ID
      await loadSessions(); // 刷新侧边栏列表
    }

    const savedUserMessage = await chatAPI.sendMessage({
      session_id: originalSessionId,
      content: userMessageContent,
      role: 'user',
      model_name: selectedModel.value || 'unknown'
    });
    // 更新用户消息 ID，便于后续定位
    userMessage.id = savedUserMessage.data.id;
  } catch (error) {
    console.error('保存用户消息失败:', error);
    ElMessage.error('无法保存您的消息，请检查网络连接');
    sending.value = false;
    return; // 保存失败则不继续
  }

  try {
    // 构建消息数组，如果选择了系统提示词则添加system消息
    const messages = [];

    // 添加系统提示词（如果选择了）
    if (selectedPrompt.value) {
      const selectedPromptData = availablePrompts.value.find(p => p.id === selectedPrompt.value);
      if (selectedPromptData) {
        messages.push({
          role: 'system',
          content: selectedPromptData.content
        });
      }
    }

    // 添加用户消息
    messages.push({
      role: 'user',
      content: userMessageContent
    });

    // 使用chat API进行对话
    const requestData = {
      model_config_id: selectedModel.value,
      messages: messages
    };

    let aiResponseContent = '';
    let originalResponseContent = ''; // 保存原始内容（包含<think>标签）
    
    // 重试机制：最多重试2次
    let retryCount = 0;
    const maxRetries = 2;
    let lastError = null;
    
    while (retryCount < maxRetries) {
      try {
        if (isStreaming.value) {
          await handleStreamingResponse(requestData, originalSessionId, (finalContent) => {
            originalResponseContent = finalContent || '';
          });
          // 获取流式响应的最终内容（用于本地变量）
          const lastMessage = currentSession.value.messages[currentSession.value.messages.length - 1];
          if (lastMessage && lastMessage.role === 'assistant') {
            aiResponseContent = lastMessage.content;
          }
          break; // 成功，跳出重试循环
        } else {
          const response = await api.post('/chat/', requestData);
          
          // 解析响应内容
          const responseContent = response.data.response || '抱歉，我无法回答这个问题。';
          originalResponseContent = responseContent; // 保存原始内容
          const parsed = parseThinkingContent(responseContent);
          
          // 添加AI回复到对话
          const assistantMessage = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: parsed.content,
            thinking: parsed.thinking,
            showThinking: parsed.hasThinking,
            created_at: new Date().toISOString()
          };
          
          // 只有当前显示的会话是原始会话时才更新UI
          if (currentSession.value.id === originalSessionId) {
            currentSession.value.messages.push(assistantMessage);
            scrollToBottom();
          }
          
          aiResponseContent = responseContent;
          break; // 成功，跳出重试循环
        }
      } catch (error) {
        retryCount++;
        lastError = error;
        console.error(`请求失败，第${retryCount}次尝试:`, error);
        
        if (retryCount < maxRetries) {
          // 等待1秒后重试
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // 移除之前的错误消息（如果存在）
          if (currentSession.value.messages.length > 0) {
            const lastMessage = currentSession.value.messages[currentSession.value.messages.length - 1];
            if (lastMessage && lastMessage.role === 'assistant' && lastMessage.isStreaming) {
              currentSession.value.messages.pop();
            }
          }
        } else {
          // 所有重试都失败，显示错误消息
          const errorMessage = {
            id: `assistant-${Date.now()}`,
            role: 'assistant',
            content: '抱歉，模型调用失败，请稍后重试。',
            isError: true,
            created_at: new Date().toISOString()
          };
          
          // 只有当前显示的会话是原始会话时才更新UI
          if (currentSession.value.id === originalSessionId) {
            currentSession.value.messages.push(errorMessage);
            scrollToBottom();
          }
          
          throw lastError; // 重新抛出最后一个错误
        }
      }
    }

    // 保存AI回复到数据库
    try {
      // 保存AI回复（使用原始会话ID）
      if (originalResponseContent) {
        console.log('💾 保存AI回复到数据库:', {
          session_id: originalSessionId,
          content_length: originalResponseContent.length,
          role: 'assistant',
          model_name: selectedModel.value || 'unknown'
        });
        const aiMessageResponse = await chatAPI.sendMessage({
          session_id: originalSessionId,
          content: originalResponseContent,
          role: 'assistant',
          model_name: selectedModel.value || 'unknown'
        });
        console.log('✅ AI回复保存成功, 消息ID:', aiMessageResponse.data?.id);
        
        // 刷新会话列表（更新时间戳）
        await loadSessions();
      } else {
        console.log('⚠️ 没有AI回复内容需要保存');
      }

    } catch (error) {
      console.error('保存聊天记录失败:', error);
    }

  } catch (error) {
    // 此处的catch只用于捕获从重试循环中最终抛出的、无法处理的错误。
    // UI更新和错误保存逻辑已在循环内部处理，这里只做日志记录。
    console.error('AI调用最终失败:', error);
  } finally {
    sending.value = false;
    scrollToBottom();
  }
};


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
      downloadMessage,
      retryMessage,
      sendMessage,
      toggleThinking,
      ChatDotRound,
      Delete,
      Reading,
      ArrowDown,
      Download,
      Refresh
    }
  }
}
</script>

<style scoped>
@import 'highlight.js/styles/atom-one-dark.css';

/* 聊天容器 */
.model-chat-container {
  height: calc(100vh - 30px - 2.4rem); /* 减去header高度和main-content的padding */
  display: flex;
  background: var(--background-blue);
  overflow: hidden;
  margin: -1.2rem; /* 抵消main-content的padding */
}

/* 左侧边栏 */
.chat-sidebar {
  width: 320px;
  background: var(--bg-color);
  border-right: 1px solid var(--border-color);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.sidebar-header {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
  background: var(--bg-color);
}

.sidebar-header .el-button {
  height: 48px;
  font-size: 16px;
  font-weight: 500;
  border-radius: 8px;
  width: 100%;
}

/* 会话列表 */
.session-list {
  flex: 1;
  padding: 16px;
}

.session-item {
  padding: 16px;
  margin-bottom: 8px;
  border-radius: 8px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.session-item:hover {
  background: var(--light-blue);
  border-color: var(--medium-blue);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.session-item.active {
  background: var(--primary-blue);
  border-color: var(--primary-blue);
  color: white;
  box-shadow: 0 2px 12px rgba(100, 168, 219, 0.3);
}

/* 流式状态指示器 */
.streaming-indicator {
  color: var(--primary-blue);
  font-size: 12px;
  margin-left: 8px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.rotating {
  animation: rotate 2s linear infinite;
}

@keyframes rotate {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

/* 思维链样式 */
.thinking-section {
  margin: 12px 0;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  background: var(--light-blue);
  overflow: hidden;
}

.thinking-header {
  padding: 12px 16px;
  background: var(--medium-blue);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: var(--text-color);
  transition: background 0.2s ease;
}

.thinking-header:hover {
  background: var(--primary-blue);
  color: white;
}

.collapse-icon {
  margin-left: auto;
  transition: transform 0.2s ease;
}

.collapse-icon.rotated {
  transform: rotate(180deg);
}

.thinking-content {
  padding: 16px;
  background: var(--light-blue);
}

.thinking-text {
  font-size: 14px;
  line-height: 1.6;
  color: var(--text-color);
  font-style: italic;
}

.session-title {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 4px;
  color: inherit;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.session-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
  color: inherit;
  opacity: 0.7;
}

.session-info .el-icon {
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: background 0.2s ease;
}

.session-info .el-icon:hover {
  background: rgba(255, 255, 255, 0.2);
}

.session-info .delete-icon {
  color: #333;
  font-size: 24px;
  opacity: 1;
  transition: all 0.2s ease;
}

.session-info .delete-icon:hover {
  color: #f56565;
  opacity: 1;
  background: rgba(245, 101, 101, 0.15);
  transform: scale(1.15);
}


/* 消息下载按钮样式 */
.message-download-area {
  margin-top: 8px;
  display: flex;
  justify-content: flex-end;
}

.message-item.user .message-download-area {
  justify-content: flex-start;
}

.download-message-btn {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 6px;
  background: var(--primary-blue);
  border: none;
  color: white;
  transition: all 0.2s ease;
}

.download-message-btn:hover {
  background: var(--medium-blue);
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(100, 168, 219, 0.3);
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
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
  min-height: 0; /* 确保flex子元素可以正确收缩 */
}

/* 聊天区域头部 */
.chat-header {
  padding: 20px 24px;
  background: var(--bg-color);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-title {
  font-size: 18px;
  font-weight: 600;
  color: var(--text-color);
}

/* 消息列表 */
.message-list {
  flex: 1;
  padding: 20px;
  background: var(--background-blue);
  min-height: 0; /* 确保可以正确收缩 */
  overflow: hidden; /* 确保内容不会溢出 */
}

.message-item {
  display: flex;
  margin-bottom: 20px;
  align-items: flex-start;
  gap: 2px;
}

.message-item.user {
  flex-direction: row-reverse;
}

.message-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  flex-shrink: 0;
}

.message-content-wrapper {
  max-width: 70%;
  display: flex;
  flex-direction: column;
}

.message-item.user .message-content-wrapper {
  align-items: flex-end;
}

.message-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  font-size: 12px;
  color: var(--text-color-secondary);
}

.message-item.user .message-info {
  flex-direction: row-reverse;
}

.message-text {
  padding: 2px 16px;
  border-radius: 16px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  color: var(--text-color);
  line-height: 1.5;
  word-wrap: break-word;
  white-space: normal;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  min-height: 20px;
  min-width: 120px;
}

.message-text :deep(p) {
  margin: 0.5em;
}

/* 空消息或流式消息的处理 */
.message-text:empty,
.message-text:has(*:empty) {
  min-height: 48px;
  min-width: 120px;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* 为空的流式消息添加占位符效果 */
.message-item.assistant .message-text:empty::after {
  content: "";
  width: 8px;
  height: 8px;
  background: var(--primary-blue);
  border-radius: 50%;
  animation: pulse 1.5s ease-in-out infinite;
  position: absolute;
}

/* 空的流式消息样式 */
.message-text.streaming-empty {
  min-height: 48px;
  min-width: 120px;
  display: flex;
  justify-content: center;
  align-items: center;
}

.streaming-placeholder {
  color: #999;
  font-style: italic;
  font-size: 14px;
}

.message-item.user .message-text {
  background: var(--primary-blue);
  color: white;
  border: none;
  border-radius: 16px 4px 16px 16px;
}

.message-item.assistant .message-text {
  border-radius: 4px 16px 16px 16px;
}

/* 输入区域 */
.chat-input-area {
  padding: 30px 24px;
  background: var(--bg-color);
  border-top: 1px solid var(--border-color);
  flex-shrink: 0; /* 防止输入区域被压缩 */
}

.input-controls {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  align-items: center;
  flex-wrap: wrap;
}

.model-selector,
.prompt-selector,
.streaming-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
  white-space: nowrap;
}

.model-select,
.prompt-select {
  min-width: 200px;
}

.message-input {
  margin-bottom: 12px;
}

.message-input :deep(.el-textarea__inner) {
  border-radius: 12px;
  border: 1px solid var(--border-color);
  padding: 16px;
  font-size: 14px;
  line-height: 1.5;
  resize: none;
  transition: border-color 0.2s ease;
}

.message-input :deep(.el-textarea__inner):focus {
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 2px rgba(100, 168, 219, 0.2);
}

.send-actions {
  display: flex;
  justify-content: flex-end;
}

.send-button {
  padding: 12px 24px;
  font-size: 14px;
  font-weight: 500;
  border-radius: 8px;
  min-width: 100px;
}

/* 欢迎区域 */
.welcome-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 40px;
  color: var(--text-color-secondary);
}

.welcome-area h2 {
  margin: 20px 0 12px;
  color: var(--text-color);
  font-size: 24px;
  font-weight: 600;
}

.welcome-area p {
  font-size: 16px;
  opacity: 0.8;
}

/* 代码高亮样式 */
.message-text :deep(pre) {
  background: #2d3748;
  border-radius: 8px;
  padding: 16px;
  margin: 12px 0;
  overflow-x: auto;
}

.message-text :deep(code) {
  background: rgba(0, 0, 0, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 13px;
}

.message-text :deep(pre code) {
  background: none;
  padding: 0;
}

/* 错误消息样式 */
.message-item.assistant .message-content-wrapper .message-text.is-error {
  background: #fef2f2;
  border: 1px solid #fecaca;
  color: #dc2626;
}

.retry-message-btn {
  margin-left: 8px;
}

/* 滚动条样式 */
.session-list :deep(.el-scrollbar__wrap) {
  scrollbar-width: thin;
  scrollbar-color: var(--border-color) transparent;
}

.session-list :deep(.el-scrollbar__wrap)::-webkit-scrollbar {
  width: 6px;
}

.session-list :deep(.el-scrollbar__wrap)::-webkit-scrollbar-track {
  background: transparent;
}

.session-list :deep(.el-scrollbar__wrap)::-webkit-scrollbar-thumb {
  background: var(--border-color);
  border-radius: 3px;
}

.session-list :deep(.el-scrollbar__wrap)::-webkit-scrollbar-thumb:hover {
  background: var(--medium-blue);
}

/* 动画定义 */
@keyframes pulse {
  0%, 100% {
    opacity: 0.4;
    transform: scale(1);
  }
  50% {
    opacity: 1;
    transform: scale(1.2);
  }
}

/* 响应式适配 */
@media (max-width: 768px) {
  .chat-sidebar {
    width: 280px;
  }

  .message-content-wrapper {
    max-width: 85%;
  }

  .input-controls {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
  }

  .model-select,
  .prompt-select {
    min-width: auto;
    width: 100%;
  }
}
</style> 