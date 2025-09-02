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
              <div v-if="message.thinking" class="thinking-section">
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
                   :class="{ 'streaming-empty': message.isStreaming && !message.content.trim() }"
                   v-html="renderMarkdown(message.content) || (message.isStreaming ? '<span class=&quot;streaming-placeholder&quot;>AI正在思考中...</span>' : '')">
              </div>

              <!-- AI消息下载按钮 -->
              <div v-if="message.role === 'assistant' && !message.isStreaming" class="message-download-area">
                <el-button
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
import {ChatDotRound, Delete, Avatar, Reading, ArrowDown, Download} from '@element-plus/icons-vue'
import {chatAPI, modelAPI, modelConfigAPI} from '../utils/api'
import {marked} from 'marked'
import hljs from 'highlight.js'
import api from '../utils/api'
import { createSSEStream } from '../utils/tokenManager'
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
    console.log('🔷 ModelChat setup函数开始执行');
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
        console.log('🔄 开始加载模型列表...')
        const response = await modelConfigAPI.getModels()
        console.log('📡 模型API响应:', response)
        
        const models = Array.isArray(response.data) ? response.data : (Array.isArray(response) ? response : [])
        console.log('📋 原始模型数据:', models)
        
        const filteredModels = models.filter(m => m.status === 1)
        console.log('✅ 过滤后的模型数据:', filteredModels)
        
        availableModels.value = filteredModels.map(config => ({
          id: config.id,
          name: `${config.providerName}: ${config.modelName}`,
          providerName: config.providerName,
          modelName: config.modelName,
          configId: config.id
        }))
        
        console.log('🎯 最终可用模型列表:', availableModels.value)
        console.log('🔍 当前选中模型:', selectedModel.value)
        
        if (availableModels.value.length > 0 && !selectedModel.value) {
          selectedModel.value = availableModels.value[0].configId
          console.log('🎯 设置默认模型:', selectedModel.value)
        }
        
        // 强制触发响应式更新
        await nextTick()
        console.log('🔄 响应式更新完成')
      } catch (error) {
        console.error('❌ 加载模型列表失败:', error)
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
        console.log('🔄 开始加载会话列表...')
        console.log('当前用户状态:', store.state.user)
        const response = await chatAPI.getSessions()
        console.log('会话API响应:', response)
        const sessions = Array.isArray(response.data) ? response.data : (Array.isArray(response) ? response : [])
        chatSessions.value = sessions

        // 如果没有当前会话且有历史会话，不自动选择第一个，让用户手动点击
        console.log(`✅ 成功加载了 ${sessions.length} 个会话`)
      } catch (error) {
        console.error('❌ 加载会话失败:', error)
        if (error.response) {
          console.error('错误响应状态:', error.response.status)
          console.error('错误响应数据:', error.response.data)
        }
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
        console.log('🔄 正在加载会话:', session.id)
        console.log('当前用户状态:', store.state.user)
        const response = await chatAPI.getSession(session.id)
        console.log('会话详情API响应:', response)

        // 确保响应数据格式正确
        const sessionDetail = response.data || response
        if (!sessionDetail || !sessionDetail.id) {
          throw new Error('会话数据格式错误')
        }

        // 确保messages是数组
        if (!Array.isArray(sessionDetail.messages)) {
          sessionDetail.messages = []
        }

        currentSession.value = sessionDetail
        console.log(`✅ 成功加载会话: ${sessionDetail.title}, 包含 ${sessionDetail.messages.length} 条消息`)

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

    const handleEnter = (e) => {
      if (!e.shiftKey && !sending.value) {
        sendMessage()
      }
    }

    const toggleThinking = (message) => {
      message.showThinking = !message.showThinking
    }

    // 解析思维链内容
    const parseThinkingContent = (content) => {
      const thinkingRegex = /<think>(.*?)<\/think>/s
      const match = content.match(thinkingRegex)

      if (match) {
        return {
          thinking: match[1].trim(),
          content: content.replace(thinkingRegex, '').trim(),
          hasThinking: true
        }
      }

      return {
        thinking: '',
        content: content,
        hasThinking: false
      }
    }

    // 处理流式响应
const handleStreamingResponse = async (requestData) => {
  console.log('🚀 开始处理流式响应请求:', requestData);

  // 创建空的助手消息
  const assistantMessage = {
    id: `assistant-${Date.now()}`,
    role: 'assistant',
    content: '',
    isStreaming: true,
    created_at: new Date().toISOString()
  };

  console.log('📝 创建空的助手消息:', assistantMessage);

  if (!currentSession.value.messages) {
    currentSession.value.messages = [];
  }
  currentSession.value.messages.push(assistantMessage);
  console.log('📥 添加空消息到会话中，当前消息数量:', currentSession.value.messages.length);
  scrollToBottom();
  console.log('⏬ 滚动到底部');

  try {
    // 使用新的SSE流式处理函数
    await createSSEStream(
      `${api.defaults.baseURL}/playground/chat/stream`,
      requestData,
      // onChunk回调：每次收到新内容时更新消息
      (currentContent) => {
        console.log('🔄 更新消息内容，长度:', currentContent.length);
        const messageIndex = currentSession.value.messages.length - 1;
        if (messageIndex >= 0) {
          currentSession.value.messages[messageIndex] = {
            ...currentSession.value.messages[messageIndex],
            content: currentContent
          };
          scrollToBottom();
        }
      },
      // onComplete回调：流式传输完成时
      (finalContent) => {
        console.log('✅ 流式传输完成，最终内容长度:', finalContent.length);
        const messageIndex = currentSession.value.messages.length - 1;
        if (messageIndex >= 0) {
          currentSession.value.messages[messageIndex] = {
            ...currentSession.value.messages[messageIndex],
            content: finalContent,
            isStreaming: false
          };
          scrollToBottom();
        }
      },
      // onError回调：发生错误时
      (error) => {
        console.error('💥 流式处理错误:', error);
        const messageIndex = currentSession.value.messages.length - 1;
        if (messageIndex >= 0) {
          currentSession.value.messages[messageIndex] = {
            ...currentSession.value.messages[messageIndex],
            content: `错误: ${error.message}`,
            isStreaming: false
          };
        }
        throw error;
      }
    );

  } catch (error) {
    console.error('🔥 流式请求处理失败:', error);

    // 移除正在流式传输的消息
    if (currentSession.value && currentSession.value.messages) {
      const messageIndex = currentSession.value.messages.findIndex(
        msg => msg.id === assistantMessage.id
      );
      if (messageIndex !== -1) {
        currentSession.value.messages.splice(messageIndex, 1);
        console.log('🗑️ 移除错误消息，索引:', messageIndex);
      }
    }

    // 重新抛出错误以便上层处理
    throw error;
  }
};
const sendMessage = async () => {
  console.log('🚀 开始发送消息流程');
  console.log('📝 输入消息内容:', inputMessage.value);
  console.log('🔄 当前流式开关状态:', isStreaming.value);
  console.log('📡 当前选中模型:', selectedModel.value);

  if (!inputMessage.value.trim() || sending.value) {
    console.log('⚠️ 消息为空或正在发送中，取消发送');
    return;
  }

  if (!selectedModel.value) {
    console.log('⚠️ 未选择模型');
    ElMessage.warning('请先选择一个对话模型');
    return;
  }

  const userMessageContent = inputMessage.value.trim();
  console.log('💬 用户消息内容:', userMessageContent);
  inputMessage.value = '';
  sending.value = true;
  console.log('🔒 设置发送状态为true');

  // 立即在前端显示用户消息
  const userMessage = {
    id: `user-${Date.now()}`,
    role: 'user',
    content: userMessageContent,
    created_at: new Date().toISOString()
  };

  if (!currentSession.value.messages) {
    currentSession.value.messages = [];
  }
  currentSession.value.messages.push(userMessage);
  console.log('📥 添加用户消息到会话');
  scrollToBottom();

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
        console.log('📎 添加系统提示词:', selectedPromptData.content);
      }
    }

    // 添加用户消息
    messages.push({
      role: 'user',
      content: userMessageContent
    });
    console.log('📋 完整消息历史:', messages);

    // 使用chat API进行对话
    const requestData = {
      model_config_id: selectedModel.value,
      messages: messages
    };
    console.log('📦 准备发送的请求数据:', requestData);

    let aiResponseContent = '';

    console.log('🧪 检查是否使用流式输出:', isStreaming.value);
    if (isStreaming.value) {
      console.log('🌊 进入流式处理分支');
      // 流式调用
      try {
        console.log('📲 调用handleStreamingResponse函数');
        await handleStreamingResponse(requestData);
        console.log('✅ 流式响应处理完成');
        // 获取流式响应的最终内容
        const lastMessage = currentSession.value.messages[currentSession.value.messages.length - 1];
        if (lastMessage && lastMessage.role === 'assistant') {
          aiResponseContent = lastMessage.content;
          console.log('📄 获取到AI响应内容，长度:', aiResponseContent.length);
        }
      } catch (streamError) {
        console.error('💥 流式请求失败，回退到普通请求:', streamError);
        // 流式请求失败，回退到普通请求
        const response = await api.post('/chat/', requestData);

        // 解析响应内容
        const responseContent = response.data.response || '抱歉，我无法回答这个问题。';
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

        currentSession.value.messages.push(assistantMessage);
        aiResponseContent = parsed.content;
        console.log('🔄 使用普通请求获取响应内容，长度:', aiResponseContent.length);
      }
    } else {
      console.log('📝 进入普通处理分支');
      // 普通调用
      const response = await api.post('/chat/', requestData);
      console.log('📬 普通请求响应:', response);

      // 解析响应内容
      const responseContent = response.data.response || '抱歉，我无法回答这个问题。';
      const parsed = parseThinkingContent(responseContent);
      console.log('🧩 解析响应内容:', parsed);

      // 添加AI回复到对话
      const assistantMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: parsed.content,
        thinking: parsed.thinking,
        showThinking: parsed.hasThinking,
        created_at: new Date().toISOString()
      };

      currentSession.value.messages.push(assistantMessage);
      aiResponseContent = parsed.content;
      console.log('📄 普通请求响应内容长度:', aiResponseContent.length);
    }

    // 保存会话和消息记录到后端
    try {
      console.log('💾 开始保存会话和消息到后端...');
      if (!currentSession.value.id) {
        // 创建新会话
        console.log('🆕 创建新会话...');
        const title = userMessageContent.length > 20
          ? userMessageContent.substring(0, 20) + '...'
          : userMessageContent;

        const sessionResponse = await chatAPI.createSession({
          title: title
        });
        console.log('🆕 新会话创建成功:', sessionResponse.data);

        // 更新当前会话信息
        currentSession.value.id = sessionResponse.data.id;
        currentSession.value.title = title;
        currentSession.value.created_at = sessionResponse.data.created_at;
        currentSession.value.updated_at = sessionResponse.data.updated_at;

        // 重新加载会话列表
        await loadSessions();
      }

      // 保存用户消息
      console.log('👤 保存用户消息...', {
        session_id: currentSession.value.id,
        content: userMessageContent,
        role: 'user',
        model_name: selectedModel.value || 'unknown'
      });
      await chatAPI.sendMessage({
        session_id: currentSession.value.id,
        content: userMessageContent,
        role: 'user',
        model_name: selectedModel.value || 'unknown'
      });
      console.log('✅ 用户消息保存成功');

      // 保存AI回复
      if (aiResponseContent) {
        console.log('🤖 保存AI回复...', {
          session_id: currentSession.value.id,
          content: aiResponseContent,
          role: 'assistant',
          model_name: selectedModel.value || 'unknown'
        });
        await chatAPI.sendMessage({
          session_id: currentSession.value.id,
          content: aiResponseContent,
          role: 'assistant',
          model_name: selectedModel.value || 'unknown'
        });
        console.log('✅ AI回复保存成功');
      }

    } catch (error) {
      console.error('❌ 保存聊天记录失败:', error);
      if (error.response) {
        console.error('📄 错误响应:', error.response.data);
      }
    }

  } catch (error) {
    console.error('💥 发送消息失败:', error);
    const errorMessage = {
      id: `error-${Date.now()}`,
      role: 'assistant',
      content: '抱歉，请求出错，请稍后重试。详细错误：' + (error.response?.data?.detail || error.message),
      created_at: new Date().toISOString()
    };
    currentSession.value.messages.push(errorMessage);
  } finally {
    sending.value = false;
    console.log('🔓 解除发送状态');
    scrollToBottom();
  }
};


    onMounted(() => {
      // 调试用户状态
      console.log('🔍 ModelChat组件挂载时的用户状态:')
      console.log('Store用户:', store.state.user)
      console.log('是否登录:', store.state.isLoggedIn)
      console.log('LocalStorage用户:', localStorage.getItem('user'))

      loadModels()
      loadPrompts()
      loadSessions()
    })

    // 监听模型选择变化
    watch(selectedModel, (newValue, oldValue) => {
      console.log('🎯 模型选择变化:', { oldValue, newValue })
    })

    // 监听可用模型列表变化
    watch(availableModels, (newValue) => {
      console.log('📋 可用模型列表变化:', newValue)
    }, { deep: true })

    // 调试函数：手动设置模型
    const debugSetModel = (modelId) => {
      console.log('🔧 手动设置模型:', modelId)
      selectedModel.value = modelId
    }

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
      sendMessage,
      toggleThinking,
      parseThinkingContent,
      debugSetModel,
      ChatDotRound,
      Delete,
      Reading,
      ArrowDown
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
  padding: 5px 16px;
  border-radius: 16px;
  background: var(--bg-color);
  border: 1px solid var(--border-color);
  color: var(--text-color);
  line-height: 1.5;
  word-wrap: break-word;
  white-space: pre-wrap; /* 保留空白字符和换行符 */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  min-height: 20px;
}

/* 空消息或流式消息的处理 */
.message-text:empty,
.message-text:has(*:empty) {
  min-height: 40px;
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
  min-height: 40px;
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