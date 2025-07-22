<template>
  <div class="model-test-container">
    <div class="header">
      <h2>模型测试</h2>
      <div class="controls">
        <el-select
          v-model="selectedModels"
          multiple
          placeholder="选择模型（最多3个）"
          style="width: 300px; margin-right: 16px"
          :max-collapse-tags="2"
        >
          <el-option
            v-for="config in availableConfigs"
            :key="config.id"
            :label="`${config.provider_name}: ${config.model_name}`"
            :value="config.id"
            :disabled="selectedModels.length >= 3 && !selectedModels.includes(config.id)"
          />
        </el-select>

        <el-select
          v-model="outputMode"
          style="width: 120px; margin-right: 16px"
        >
          <el-option label="普通输出" value="normal" />
          <el-option label="流式输出" value="streaming" />
        </el-select>

        <el-button
          type="danger"
          :disabled="!hasConversations"
          @click="clearAllConversations"
          icon="Delete"
        >
          清空对话
        </el-button>
      </div>
    </div>

    <!-- 模型对话区域 -->
    <div class="chat-area" v-if="selectedModels.length > 0">
      <el-row :gutter="16">
        <el-col 
          :span="selectedModels.length === 1 ? 24 : selectedModels.length === 2 ? 12 : 8"
          v-for="modelId in selectedModels"
          :key="modelId"
        >
          <el-card class="model-chat-card">
            <template #header>
              <div class="model-header">
                <span>{{ getModelName(modelId) }}</span>
                <el-icon v-if="loading[modelId]" class="is-loading">
                  <Loading />
                </el-icon>
              </div>
            </template>

            <div class="chat-messages" ref="chatContainers">
              <div 
                v-for="(message, index) in conversations[modelId] || []"
                :key="index"
                class="message"
                :class="message.role"
              >
                <div class="message-content">
                  <!-- 用户消息 -->
                  <div v-if="message.role === 'user'" class="user-message">
                    <div v-if="typeof message.content === 'string'">
                      {{ message.content }}
                    </div>
                    <div v-else-if="Array.isArray(message.content)">
                      <div v-for="(item, i) in message.content" :key="i">
                        <p v-if="item.type === 'text'">{{ item.text }}</p>
                        <img 
                          v-if="item.type === 'image_url'" 
                          :src="item.image_url.url" 
                          alt="上传图片"
                          class="uploaded-image"
                        />
                      </div>
                    </div>
                  </div>

                  <!-- 助手消息 -->
                  <div v-if="message.role === 'assistant'" class="assistant-message">
                    <!-- 推理过程 -->
                    <div v-if="message.thinking && message.showThinking" class="thinking-section">
                      <el-collapse v-model="expandedThinking[`${modelId}-${index}`]">
                        <el-collapse-item name="thinking">
                          <template #title>
                            <el-icon><Cpu /></el-icon>
                            <span style="margin-left: 8px">推理过程</span>
                          </template>
                          <div class="thinking-content">{{ message.thinking }}</div>
                        </el-collapse-item>
                      </el-collapse>
                    </div>

                    <!-- 回答内容 -->
                    <div class="answer-content">
                      <div v-if="message.isStreaming" class="streaming-indicator">
                        <el-icon class="is-loading"><Loading /></el-icon>
                        <span>生成中...</span>
                      </div>
                      <div v-html="formatMessage(message.content)"></div>
                    </div>
                  </div>

                  <!-- 错误消息 -->
                  <div v-if="message.role === 'error'" class="error-message">
                    <el-alert :title="message.content" type="error" show-icon :closable="false" />
                  </div>
                </div>
              </div>

              <div v-if="(conversations[modelId] || []).length === 0" class="empty-chat">
                <el-empty description="发送第一条消息开始测试" />
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <el-empty description="请选择至少一个模型开始测试" />
    </div>

    <!-- 输入区域 -->
    <div class="input-area" v-if="selectedModels.length > 0">
      <!-- 图片预览 -->
      <div v-if="uploadedImage" class="image-preview">
        <div class="image-container">
          <img :src="uploadedImage" alt="上传图片" />
          <el-button
            size="small"
            type="danger"
            circle
            icon="Close"
            class="remove-image"
            @click="removeImage"
          />
        </div>
      </div>

      <div class="input-controls">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          placeholder="输入消息..."
          @keydown.ctrl.enter="sendMessage"
          :disabled="isLoading"
        />
        
        <div class="input-actions">
          <!-- 图片上传按钮（仅当选择了视觉模型时显示） -->
          <el-upload
            v-if="hasVisionModel"
            :show-file-list="false"
            :before-upload="beforeImageUpload"
            accept="image/*"
            :disabled="isLoading"
          >
            <el-button icon="Picture" :disabled="isLoading">
              上传图片
            </el-button>
          </el-upload>

          <el-button
            type="primary"
            @click="sendMessage"
            :disabled="isSendDisabled"
            :loading="isLoading"
            icon="Promotion"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive, computed, nextTick, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Loading, Cpu, Picture, Delete, Promotion, Close } from '@element-plus/icons-vue'
import api from '@/utils/api'

export default {
  name: 'ModelTest',
  components: {
    Loading,
    Cpu,
    Picture,
    Delete,
    Promotion,
    Close
  },
  setup() {
    const availableConfigs = ref([])
    const selectedModels = ref([])
    const conversations = reactive({})
    const loading = reactive({})
    const userInput = ref('')
    const uploadedImage = ref(null)
    const outputMode = ref('normal')
    const expandedThinking = reactive({})
    const chatContainers = ref([])

    // 计算属性
    const isLoading = computed(() => Object.values(loading).some(v => v))
    const isSendDisabled = computed(() => 
      isLoading.value || 
      selectedModels.value.length === 0 || 
      (!userInput.value.trim() && !uploadedImage.value)
    )
    const hasConversations = computed(() => 
      selectedModels.value.some(modelId => 
        conversations[modelId] && conversations[modelId].length > 0
      )
    )
    const hasVisionModel = computed(() =>
      selectedModels.value.some(modelId => {
        const config = availableConfigs.value.find(c => c.id === modelId)
        return config && config.type === 'vision'
      })
    )

    // 获取模型配置列表
    const fetchModelConfigs = async () => {
      try {
        const response = await api.get('/model-config/')
        availableConfigs.value = response.data.filter(config => 
          config.model_name && 
          config.endpoint && 
          config.status === 1  // 只显示启用的配置
        )
      } catch (error) {
        message.error('获取模型配置失败')
      }
    }

    // 获取模型名称
    const getModelName = (modelId) => {
      const config = availableConfigs.value.find(c => c.id === modelId)
      return config ? `${config.provider_name}: ${config.model_name}` : modelId
    }

    // 图片上传前处理
    const beforeImageUpload = (file) => {
      const isImage = file.type.startsWith('image/')
      const isLt5M = file.size / 1024 / 1024 < 5

      if (!isImage) {
        message.error('只能上传图片文件!')
        return false
      }
      if (!isLt5M) {
        message.error('图片大小不能超过 5MB!')
        return false
      }

      // 转换为base64
      const reader = new FileReader()
      reader.onload = (e) => {
        uploadedImage.value = e.target.result
      }
      reader.readAsDataURL(file)
      
      return false // 阻止自动上传
    }

    // 移除图片
    const removeImage = () => {
      uploadedImage.value = null
    }

    // 发送消息
    const sendMessage = async () => {
      if (isSendDisabled.value) return

      const input = userInput.value.trim()
      const image = uploadedImage.value

      // 清空输入
      userInput.value = ''
      uploadedImage.value = null

      // 为每个选中的模型添加用户消息
      selectedModels.value.forEach(modelId => {
        if (!conversations[modelId]) {
          conversations[modelId] = []
        }

        const config = availableConfigs.value.find(c => c.id === modelId)
        const isVisionModel = config && config.type === 'vision'

        if (isVisionModel && image) {
          conversations[modelId].push({
            role: 'user',
            content: [
              { type: 'text', text: input || '请描述这个图片' },
              { type: 'image_url', image_url: { url: image } }
            ]
          })
        } else {
          conversations[modelId].push({
            role: 'user',
            content: input
          })
        }
      })

      // 为每个模型设置加载状态
      selectedModels.value.forEach(modelId => {
        loading[modelId] = true
      })

      // 为每个模型发送请求
      const promises = selectedModels.value.map(async (modelId) => {
        const config = availableConfigs.value.find(c => c.id === modelId)
        if (!config) {
          conversations[modelId].push({
            role: 'error',
            content: '模型配置不存在'
          })
          loading[modelId] = false
          return
        }

        try {
          const messages = conversations[modelId].slice() // 复制消息历史

          if (outputMode.value === 'streaming') {
            await handleStreamingResponse(modelId, messages)
          } else {
            await handleNormalResponse(modelId, messages)
          }
        } catch (error) {
          conversations[modelId].push({
            role: 'error',
            content: `错误: ${error.message}`
          })
        } finally {
          loading[modelId] = false
        }
      })

      await Promise.all(promises)
      scrollToBottom()
    }

    // 处理普通响应
    const handleNormalResponse = async (modelId, messages) => {
      const response = await api.post('/playground/chat', {
        model_config_id: modelId,
        messages: messages
      })

      const responseText = response.data.response
      let thinking = ''
      let content = responseText

      // 解析推理链
      if (responseText.includes('<think>') && responseText.includes('</think>')) {
        const thinkMatch = responseText.match(/<think>(.*?)<\/think>/s)
        if (thinkMatch) {
          thinking = thinkMatch[1].trim()
          content = responseText.replace(/<think>.*?<\/think>/s, '').trim()
        }
      }

      conversations[modelId].push({
        role: 'assistant',
        content: content,
        thinking: thinking,
        showThinking: !!thinking
      })
    }

    // 处理流式响应
    const handleStreamingResponse = async (modelId, messages) => {
      // 添加空的助手消息用于流式更新
      conversations[modelId].push({
        role: 'assistant',
        content: '',
        thinking: '',
        showThinking: false,
        isStreaming: true
      })

      const response = await fetch(`${api.defaults.baseURL}/playground/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          model_config_id: modelId,
          messages: messages
        })
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()

      let isInThinking = false
      let currentThinking = ''
      let currentContent = ''

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        const chunk = decoder.decode(value, { stream: true })

        // 处理思维链标签
        for (let i = 0; i < chunk.length; i++) {
          const char = chunk[i]

          if (i + 6 <= chunk.length && chunk.substring(i, i + 7) === '<think>') {
            isInThinking = true
            i += 6
            continue
          }

          if (i + 7 <= chunk.length && chunk.substring(i, i + 8) === '</think>') {
            isInThinking = false
            i += 7
            continue
          }

          if (isInThinking) {
            currentThinking += char
          } else {
            currentContent += char
          }
        }

        // 更新对话内容
        const lastMessage = conversations[modelId][conversations[modelId].length - 1]
        lastMessage.content = currentContent
        lastMessage.thinking = currentThinking
        lastMessage.showThinking = currentThinking.length > 0

        scrollToBottom()
      }

      // 完成流式传输
      const lastMessage = conversations[modelId][conversations[modelId].length - 1]
      lastMessage.isStreaming = false
    }

    // 清空所有对话
    const clearAllConversations = () => {
      selectedModels.value.forEach(modelId => {
        conversations[modelId] = []
      })
    }

    // 格式化消息内容
    const formatMessage = (content) => {
      if (!content) return ''
      return content.replace(/\n/g, '<br>')
    }

    // 滚动到底部
    const scrollToBottom = async () => {
      await nextTick()
      chatContainers.value.forEach(container => {
        if (container) {
          container.scrollTop = container.scrollHeight
        }
      })
    }

    onMounted(() => {
      fetchModelConfigs()
    })

    return {
      availableConfigs,
      selectedModels,
      conversations,
      loading,
      userInput,
      uploadedImage,
      outputMode,
      expandedThinking,
      chatContainers,
      isLoading,
      isSendDisabled,
      hasConversations,
      hasVisionModel,
      getModelName,
      beforeImageUpload,
      removeImage,
      sendMessage,
      clearAllConversations,
      formatMessage
    }
  }
}
</script>

<style scoped>
.model-test-container {
  padding: 20px;
  height: calc(100vh - 120px);
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.controls {
  display: flex;
  align-items: center;
}

.chat-area {
  flex: 1;
  overflow: hidden;
  margin-bottom: 20px;
}

.model-chat-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: 500;
}

.chat-messages {
  height: 400px;
  overflow-y: auto;
  padding: 16px;
}

.message {
  margin-bottom: 16px;
}

.message.user .message-content {
  display: flex;
  justify-content: flex-end;
}

.user-message {
  background: #409eff;
  color: white;
  padding: 12px 16px;
  border-radius: 16px 16px 4px 16px;
  max-width: 80%;
  word-wrap: break-word;
}

.assistant-message {
  background: #f5f7fa;
  padding: 12px 16px;
  border-radius: 16px 16px 16px 4px;
  max-width: 80%;
}

.thinking-section {
  margin-bottom: 12px;
}

.thinking-content {
  background: #fff3cd;
  padding: 12px;
  border-radius: 8px;
  border-left: 4px solid #ffc107;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 12px;
  white-space: pre-wrap;
}

.answer-content {
  white-space: pre-wrap;
}

.streaming-indicator {
  display: flex;
  align-items: center;
  color: #909399;
  font-size: 12px;
  margin-bottom: 8px;
}

.error-message {
  max-width: 80%;
}

.uploaded-image {
  max-width: 200px;
  border-radius: 8px;
  margin-top: 8px;
}

.empty-state, .empty-chat {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 200px;
}

.input-area {
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.image-preview {
  margin-bottom: 12px;
}

.image-container {
  position: relative;
  display: inline-block;
}

.image-container img {
  max-width: 200px;
  max-height: 150px;
  border-radius: 8px;
}

.remove-image {
  position: absolute;
  top: -8px;
  right: -8px;
}

.input-controls {
  display: flex;
  gap: 12px;
}

.input-controls .el-textarea {
  flex: 1;
}

.input-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
</style> 