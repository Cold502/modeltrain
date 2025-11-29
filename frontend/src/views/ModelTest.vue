<template>
  <div class="model-test-container">
    <div class="header">
      <h2>模型测试</h2>
      <div class="controls">
        <el-select
          ref="modelSelectRef"
          v-model="selectedModels"
          multiple
          placeholder="选择模型（最多3个）"
          style="width: 300px; margin-right: 16px"
          :max-collapse-tags="2"
        >
          <el-option
            v-for="config in availableConfigs"
            :key="config.id"
            :label="`${config.providerName}: ${config.modelName}`"
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

    <!-- 模型对话区域：统一使用单一聊天卡片，根据是否选择模型展示不同内容 -->
    <div class="chat-area">
      <el-card class="model-chat-card unified-card">
        <template #header>
          <div class="model-header">
            <div class="model-header-main">
              <span class="model-header-title">
                {{ selectedModels.length > 0 ? `已选择 ${selectedModels.length} 个模型` : '未选择模型' }}
              </span>
              <span v-if="selectedModels.length === 1" class="model-header-sub">{{ getModelName(selectedModels[0]) }}</span>
            </div>
            <div class="model-header-extra">
              <span class="model-header-tip">
                {{ selectedModels.length > 0 ? '发送消息对比不同模型的回答' : '请先在右上角选择要测试的模型' }}
              </span>
            </div>
          </div>
        </template>

        <!-- 未选择模型：展示统一的空状态 -->
        <div v-if="selectedModels.length === 0" class="empty-chat enhanced">
          <div class="empty-guidance">
            <el-icon class="empty-icon">
              <Promotion />
            </el-icon>
            <h3>尚未选择模型</h3>
            <p>先在右上角选择 1-3 个模型，即可在此对比不同模型的回答表现。</p>
            <el-button type="primary" size="large" @click="focusModelSelect">
              去选择模型
            </el-button>
          </div>
          <div class="empty-steps">
            <div class="empty-step">
              <span class="step-index">1</span>
              <div>
                <h4>挑选模型</h4>
                <p>支持同时选择最多 3 个，方便横向对比。</p>
              </div>
            </div>
            <div class="empty-step">
              <span class="step-index">2</span>
              <div>
                <h4>输入提示词</h4>
                <p>可直接输入文本，也可以插入常用话术或上传图片。</p>
              </div>
            </div>
            <div class="empty-step">
              <span class="step-index">3</span>
              <div>
                <h4>对比结果</h4>
                <p>查看不同模型在同一问题下的思考过程与输出。</p>
              </div>
            </div>
          </div>
        </div>

        <!-- 已选择模型：展示多模型对话列，每个模型使用独立小卡片，列间露出背景作为分隔 -->
        <div v-else>
          <el-row :gutter="16" class="model-row">
            <el-col 
              :span="selectedModels.length === 1 ? 24 : selectedModels.length === 2 ? 12 : 8"
              v-for="modelId in selectedModels"
              :key="modelId"
            >
              <el-card class="model-column-card" shadow="never">
                <div class="model-column">
                  <div class="model-column-header">
                    <span class="model-name">{{ getModelName(modelId) }}</span>
                    <el-icon v-if="loading[modelId]" class="is-loading">
                      <Loading />
                    </el-icon>
                  </div>

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
                </div>
              </el-card>
            </el-col>
          </el-row>
        </div>
      </el-card>
    </div>

    <!-- 输入区域 -->
    <div class="input-area">
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

      <div class="input-bar">
        <el-input
          v-model="userInput"
          type="textarea"
          :rows="3"
          placeholder="输入消息... (Enter发送，Shift+Enter换行)"
          @keydown.enter="handleEnter"
          :disabled="isLoading"
          class="input-bar-textarea"
        />

        <div class="input-bar-actions">
          <el-button 
            class="input-bar-button reset-button" 
            :disabled="isLoading"
            @click="resetInputAndConversation"
          >
            重置
          </el-button>

          <el-popover
            v-model:visible="questionPopoverVisible"
            placement="top-start"
            width="360"
            trigger="click"
            popper-class="question-popover"
          >
            <div class="question-popover-header">
              <el-input
                v-model="questionSearch"
                placeholder="搜索话术..."
                size="small"
                clearable
              />
              <el-button type="primary" size="small" @click.stop="openQuestionEditor()">新增</el-button>
            </div>
            <el-scrollbar class="question-popover-list">
              <div v-if="filteredQuestions.length === 0" class="question-empty">
                <el-empty description="暂无话术" :image-size="60" />
              </div>
              <div v-else>
                <div
                  v-for="question in filteredQuestions"
                  :key="question.id"
                  class="question-item"
                >
                  <div class="question-item-main" @click="useQuestion(question)">
                    <div class="question-item-header">
                      <h4>{{ question.title }}</h4>
                      <el-tag size="small" :type="question.created_by ? 'primary' : 'info'">
                        {{ question.created_by ? '我的' : '系统' }}
                      </el-tag>
                    </div>
                    <p>{{ question.content }}</p>
                  </div>
                  <div class="question-item-actions" v-if="question.created_by">
                    <el-button text type="primary" size="small" @click.stop="openQuestionEditor(question)">编辑</el-button>
                    <el-button text type="danger" size="small" @click.stop="deleteQuestion(question)">删除</el-button>
                  </div>
                </div>
              </div>
            </el-scrollbar>
            <template #reference>
              <el-button class="input-bar-button manage-button">问题管理</el-button>
            </template>
          </el-popover>

          <el-upload
            v-if="hasVisionModel"
            :show-file-list="false"
            :before-upload="beforeImageUpload"
            accept="image/*"
            :disabled="isLoading"
            class="input-bar-upload"
          >
            <el-button icon="Picture" :disabled="isLoading" class="input-bar-button">
              上传图片
            </el-button>
          </el-upload>

          <el-button
            type="primary"
            @click="sendMessage"
            :disabled="isSendDisabled"
            :loading="isLoading"
            icon="Promotion"
            class="input-bar-button send-button"
          >
            发送
          </el-button>
        </div>
      </div>
    </div>

    <!-- 新增/编辑话术弹窗 -->
    <el-dialog
      v-model="questionEditorVisible"
      :title="editingQuestion ? '编辑话术' : '新增话术'"
      width="500px"
      :close-on-click-modal="false"
    >
      <el-form :model="questionForm" label-width="64px">
        <el-form-item label="标题">
          <el-input v-model="questionForm.title" placeholder="给这个话术起个名字" />
        </el-form-item>
        <el-form-item label="内容">
          <el-input
            v-model="questionForm.content"
            type="textarea"
            :rows="4"
            placeholder="输入常用问题或提示词"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="questionEditorVisible = false">取 消</el-button>
        <el-button type="primary" :loading="questionSaving" @click="saveQuestion">保 存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, nextTick, onMounted, onBeforeUnmount, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

import { Loading, Cpu, Picture, Delete, Promotion, Close } from '@element-plus/icons-vue'
import api from '@/utils/api'
import { createSSEStream } from '@/utils/tokenManager'

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
    const modelSelectRef = ref(null)
    const availableConfigs = ref([])
    const selectedModels = ref([])
    const conversations = reactive({})
    const loading = reactive({})
    const userInput = ref('')
    const uploadedImage = ref(null)
    const outputMode = ref('normal')
    const expandedThinking = reactive({})
    const chatContainers = ref([])
    const questionPopoverVisible = ref(false)
    const questionEditorVisible = ref(false)
    const questions = ref([])
    const questionSearch = ref('')
    const questionForm = reactive({ id: null, title: '', content: '' })
    const editingQuestion = ref(null)
    const questionLoading = ref(false)
    const questionSaving = ref(false)
    let questionSearchTimer = null

    // 获取话术列表
    const fetchQuestions = async () => {
      try {
        questionLoading.value = true
        const keyword = questionSearch.value.trim()
        const response = await api.get('/playground/prompts', {
          params: { keyword: keyword || undefined }
        })
        questions.value = response.data
      } catch (error) {
        console.error('获取话术列表失败:', error)
        ElMessage.error('获取话术列表失败')
      } finally {
        questionLoading.value = false
      }
    }

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

    const filteredQuestions = computed(() => {
      if (!questionSearch.value.trim()) return questions.value
      const keyword = questionSearch.value.toLowerCase()
      return questions.value.filter(q => {
        const title = q.title?.toLowerCase() || ''
        const content = q.content?.toLowerCase() || ''
        return title.includes(keyword) || content.includes(keyword)
      })
    })

    // 获取模型配置列表
    const fetchModelConfigs = async () => {
      try {
        const response = await api.get('/model-config/')
        availableConfigs.value = response.data.filter(config => 
          config.modelName &&
          config.endpoint &&
          config.status === 1  // 只显示启用的配置
        )
        console.log(response.data)
      } catch (error) {
        message.error('获取模型配置失败')
      }
    }

    // 获取模型名称
    const getModelName = (modelId) => {
      const config = availableConfigs.value.find(c => c.id === modelId)
      return config ? `${config.providerName}: ${config.modelName}` : modelId
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

    // 重置输入和对话
    const resetInputAndConversation = () => {
      userInput.value = ''
      uploadedImage.value = null
      selectedModels.value.forEach(modelId => {
        conversations[modelId] = []
      })
    }

    // 发送消息
    const sendMessage = async () => {
      if (selectedModels.value.length === 0) {
        ElMessage.warning('请先选择至少一个模型')
        return
      }

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

      try {
        // 使用新的SSE流式处理函数
        await createSSEStream(
          `${api.defaults.baseURL}/playground/chat/stream`,
          {
            model_config_id: modelId,
            messages: messages
          },
          // onChunk回调：每次收到新内容时更新消息
          (currentContent) => {
            const lastMessage = conversations[modelId][conversations[modelId].length - 1]
            
            // 检查是否包含思维链标签
            if (currentContent.includes('<think>') && currentContent.includes('</think>')) {
              const thinkMatch = currentContent.match(/<think>(.*?)<\/think>/s)
              if (thinkMatch) {
                lastMessage.thinking = thinkMatch[1]
                lastMessage.content = currentContent.replace(/<think>.*?<\/think>/s, '')
                lastMessage.showThinking = true
              } else {
                lastMessage.content = currentContent
              }
            } else {
              lastMessage.content = currentContent
            }
            
            scrollToBottom()
          },
          // onComplete回调：流式传输完成时
          (finalContent) => {
            const lastMessage = conversations[modelId][conversations[modelId].length - 1]
            lastMessage.isStreaming = false
            
            // 最终处理思维链
            if (finalContent.includes('<think>') && finalContent.includes('</think>')) {
              const thinkMatch = finalContent.match(/<think>(.*?)<\/think>/s)
              if (thinkMatch) {
                lastMessage.thinking = thinkMatch[1]
                lastMessage.content = finalContent.replace(/<think>.*?<\/think>/s, '')
                lastMessage.showThinking = true
              } else {
                lastMessage.content = finalContent
              }
            } else {
              lastMessage.content = finalContent
            }
            
            scrollToBottom()
          },
          // onError回调：发生错误时
          (error) => {
            const lastMessage = conversations[modelId][conversations[modelId].length - 1]
            lastMessage.content = `错误: ${error.message}`
            lastMessage.isStreaming = false
            throw error
          }
        )

      } catch (error) {
        console.error('🔥 流式请求处理失败:', error)
        // 移除错误消息
        conversations[modelId].pop()
        throw error
      }
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

    // 处理回车键
    const handleEnter = (e) => {
      if (!e.shiftKey && !isLoading.value) {
        e.preventDefault()
        sendMessage()
      }
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

    // 问题管理相关
    const resetQuestionForm = () => {
      questionForm.id = null
      questionForm.title = ''
      questionForm.content = ''
    }

    const openQuestionEditor = (question = null) => {
      questionPopoverVisible.value = false
      if (question) {
        editingQuestion.value = question
        questionForm.id = question.id
        questionForm.title = question.title
        questionForm.content = question.content
      } else {
        editingQuestion.value = null
        resetQuestionForm()
      }
      questionEditorVisible.value = true
    }

    const saveQuestion = async () => {
      if (!questionForm.title.trim() || !questionForm.content.trim()) {
        ElMessage.warning('标题和内容不能为空')
        return
      }

      try {
        questionSaving.value = true
        if (editingQuestion.value) {
          // 更新
          await api.put(`/playground/prompts/${editingQuestion.value.id}`, {
            title: questionForm.title,
            content: questionForm.content
          })
          ElMessage.success('更新成功')
        } else {
          // 新增
          await api.post('/playground/prompts', {
            title: questionForm.title,
            content: questionForm.content
          })
          ElMessage.success('创建成功')
        }
        
        questionEditorVisible.value = false
        resetQuestionForm()
        editingQuestion.value = null
        await fetchQuestions() // 刷新列表
      } catch (error) {
        console.error('保存话术失败:', error)
        ElMessage.error(error.response?.data?.detail || '保存失败')
      } finally {
        questionSaving.value = false
      }
    }

    const deleteQuestion = async (question) => {
      try {
        await ElMessageBox.confirm(
          `确定删除「${question.title}」吗？删除后不可恢复。`,
          '删除确认',
          {
            confirmButtonText: '删除',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )
        await api.delete(`/playground/prompts/${question.id}`)
        ElMessage.success('删除成功')
        await fetchQuestions() // 刷新列表
      } catch (error) {
        if (error === 'cancel') return
        console.error('删除话术失败:', error)
        ElMessage.error(error.response?.data?.detail || '删除失败')
      }
    }

    const useQuestion = (question) => {
      const content = question.content?.trim()
      if (!content) return

      if (userInput.value.trim()) {
        userInput.value = `${userInput.value.trimEnd()}\n\n${content}`
      } else {
        userInput.value = content
      }

      questionPopoverVisible.value = false
      ElMessage.success('已插入话术')
    }

    const focusModelSelect = () => {
      if (modelSelectRef.value) {
        modelSelectRef.value.focus?.()
        modelSelectRef.value.toggleMenu?.()
      }
    }

    onMounted(() => {
      fetchModelConfigs()
      fetchQuestions()
    })

    // 监听搜索变化（popover打开时才触发）
    watch(questionSearch, (value) => {
      if (!questionPopoverVisible.value) return
      if (questionSearchTimer) {
        clearTimeout(questionSearchTimer)
      }
      questionSearchTimer = setTimeout(() => {
        fetchQuestions()
      }, 300)
    })

    watch(questionPopoverVisible, (visible) => {
      if (visible) {
        fetchQuestions()
      } else {
        questionSearch.value = ''
      }
    })

    onBeforeUnmount(() => {
      if (questionSearchTimer) {
        clearTimeout(questionSearchTimer)
      }
    })

    return {
      modelSelectRef,
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
      questionPopoverVisible,
      questionEditorVisible,
      questionLoading,
      questionSaving,
      questions,
      questionSearch,
      questionForm,
      editingQuestion,
      filteredQuestions,
      openQuestionEditor,
      saveQuestion,
      deleteQuestion,
      useQuestion,
      getModelName,
      beforeImageUpload,
      removeImage,
      resetInputAndConversation,
      sendMessage,
      clearAllConversations,
      formatMessage,
      handleEnter,
      focusModelSelect
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
  height: 300px;
}

.empty-chat.enhanced {
  border: 1px dashed #d5deff;
  border-radius: 12px;
  background: linear-gradient(135deg, #f9fbff 0%, #f1f5ff 100%);
  padding: 40px;
  min-height: 500px;
  align-items: stretch;
  gap: 40px;
}

.empty-guidance {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 20px;
}

.empty-guidance h3 {
  margin: 0;
  font-size: 24px;
  color: #1f2d3d;
}

.empty-guidance p {
  margin: 0;
  color: #4a5568;
  line-height: 1.8;
}

.empty-icon {
  font-size: 40px;
  color: #3a7afe;
}

.empty-steps {
  width: 400px;
  display: flex;
  flex-direction: column;
  gap: 24px;
  justify-content: center;
}

.empty-step {
  display: flex;
  gap: 16px;
  padding: 24px;
  border-radius: 12px;
  background: #fff;
  box-shadow: 0 4px 20px rgba(90, 125, 230, 0.12);
  transition: transform 0.2s;
}

.empty-step:hover {
  transform: translateY(-2px);
}

.step-index {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #3a7afe;
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
}

.empty-step h4 {
  margin: 0;
  font-size: 18px;
  color: #1f2d3d;
  margin-bottom: 8px;
}

.empty-step p {
  margin: 0;
  font-size: 16px;
  color: #4a5568;
  line-height: 1.6;
}

.input-area {
  border-top: 1px solid #ebeef5;
  padding: 16px 0 0;
}

.input-bar {
  display: flex;
  align-items: stretch;
  gap: 20px;
  padding-right: 16px;
}

.input-bar-textarea {
  flex: 1;
}

.input-bar-textarea :deep(.el-textarea__inner) {
  border-radius: 8px;
  resize: none;
  height: 140px;
}

.input-bar-actions {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: stretch;
  gap: 12px;
  width: 150px;
  padding-right: 6px;
}

.input-bar-actions :deep(.el-popover__reference-wrapper) {
  width: 100%;
  display: block;
}

.input-bar-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.input-bar-actions :deep(.el-button) {
  display: block;
  width: 100%;
}

.input-bar-button {
  width: 100%;
  height: 40px;
  border-radius: 8px;
  padding: 0 12px;
}

.reset-button {
  background: #f3f5f7;
  border-color: #dfe4ea;
  color: #2f3a4a;
}

.reset-button:hover {
  background: #e8ebf0;
  border-color: #cfd6df;
}

.manage-button {
  background: #e8f2ff;
  border-color: #c5dafc;
  color: #1f5fbf;
}

.manage-button:hover {
  background: #d8e9ff;
  border-color: #a9c7fb;
}

.send-button {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: #fff;
}

:global(.dark-mode) .model-test-container .reset-button {
  background: #2a2f37;
  border-color: #3a404c;
  color: #e6e9ef;
}

:global(.dark-mode) .model-test-container .reset-button:hover {
  background: #323845;
  border-color: #4a5262;
}

:global(.dark-mode) .model-test-container .manage-button {
  background: rgba(58, 122, 254, 0.18);
  border-color: rgba(58, 122, 254, 0.45);
  color: #a7c8ff;
}

:global(.dark-mode) .model-test-container .manage-button:hover {
  background: rgba(58, 122, 254, 0.26);
  border-color: rgba(58, 122, 254, 0.6);
}

:global(.dark-mode) .model-test-container .send-button {
  background: var(--el-color-primary);
  border-color: var(--el-color-primary);
  color: #fff;
}

.send-button {
  font-weight: 500;
}

.secondary-button {
  border-color: #dcdfe6;
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

.question-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.question-search {
  width: 260px;
}

.question-table {
  max-height: 320px;
}

::v-deep(.question-popover) {
  padding: 12px;
  border-radius: 10px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.15);
}

.question-popover-header {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.question-popover-list {
  max-height: 320px;
}

.question-item {
  padding: 12px;
  border: 1px solid #eef2ff;
  border-radius: 8px;
  background: #f8fbff;
  margin-bottom: 8px;
  transition: border-color 0.2s ease, box-shadow 0.2s ease;
}

.question-item:hover {
  border-color: #c7d7fe;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.question-item-main {
  cursor: pointer;
}

.question-item-main h4 {
  margin: 0;
  font-size: 14px;
  color: #1f2d3d;
}

.question-item-main p {
  margin: 4px 0 0;
  font-size: 13px;
  color: #4a5568;
  line-height: 1.4;
}

.question-item-actions {
  display: flex;
  gap: 8px;
  margin-top: 6px;
}

.question-empty {
  padding: 24px 0;
}

:global(.dark-mode) .model-test-container {
  background: #0d111c;
  color: #e4e9f5;
}

:global(.dark-mode) .model-test-container .header,
:global(.dark-mode) .model-test-container .input-area {
  background: transparent;
  border-color: #1f2533;
}

:global(.dark-mode) .model-test-container .unified-card,
:global(.dark-mode) .model-test-container .model-column-card,
:global(.dark-mode) .model-test-container .model-chat-card {
  background: #151b2c !important;
  border-color: #242c3f !important;
  box-shadow: none;
}

:global(.dark-mode) .model-test-container .model-column {
  background: transparent;
}

:global(.dark-mode) .model-test-container .chat-messages {
  background: #111623;
  border-radius: 12px;
}

:global(.dark-mode) .model-test-container .empty-chat.enhanced {
  background: linear-gradient(135deg, rgba(23, 32, 48, 0.9) 0%, rgba(18, 26, 40, 0.95) 100%) !important;
  border-color: #23304a !important;
}

:global(.dark-mode) .model-test-container .empty-chat.enhanced .empty-guidance h3 {
  color: #f4f7ff !important;
}

:global(.dark-mode) .model-test-container .empty-chat.enhanced .empty-guidance p,
:global(.dark-mode) .model-test-container .empty-chat.enhanced .empty-step p,
:global(.dark-mode) .model-test-container .empty-chat.enhanced .empty-step h4,
:global(.dark-mode) .model-test-container .model-header-tip {
  color: #c0cae5 !important;
}

:global(.dark-mode) .model-test-container .empty-chat.enhanced .empty-step {
  background: #1b2233 !important;
  border-color: #242f49 !important;
  box-shadow: none !important;
}

:global(.dark-mode) .model-test-container .empty-chat.enhanced .empty-step:hover {
  transform: translateY(-2px);
  border-color: #2f3d5f !important;
}

:global(.dark-mode) .model-test-container .empty-chat.enhanced .step-index {
  background: #4a7afe !important;
  color: #fff !important;
}

:global(.dark-mode) .model-test-container .empty-chat.enhanced .empty-icon {
  color: #6fa0ff !important;
}

:global(.dark-mode) .model-test-container .input-bar-textarea :deep(.el-textarea__inner) {
  background: #111723;
  border-color: #262f43;
  color: #f2f6ff;
}

:global(.dark-mode) .model-test-container .input-bar-actions {
  border-color: transparent;
}

:global(.dark-mode) .model-test-container .question-popover-header .el-input :deep(.el-input__wrapper) {
  background: #0f1522;
  border-color: #273554;
}

:global(.dark-mode) .model-test-container .question-item {
  background: #141a2a;
  border-color: #252f48;
}

:global(.dark-mode) .model-test-container .question-item:hover {
  border-color: #37507d;
  box-shadow: 0 4px 16px rgba(28, 60, 115, 0.35);
}

:global(.dark-mode) .model-test-container .question-popover-header + .question-popover-list,
:global(.dark-mode) .model-test-container .question-popover-header,
:global(.dark-mode) .model-test-container .question-popover-list {
  background: transparent;
}

:global(.dark-mode) .model-test-container .question-item-main h4 {
  color: #f4f6ff;
}

:global(.dark-mode) .model-test-container .question-item-main p {
  color: #c2cbe4;
}

:global(.dark-mode) .model-test-container .question-popover {
  background: #0f1522 !important;
  border: 1px solid #2a3550;
}

:global(.dark-mode) .model-test-container .question-item-actions .el-button[text] {
  color: #8fb4ff;
}

:global(.dark-mode) .model-test-container .el-empty__description {
  color: #b8c1da;
}

</style>