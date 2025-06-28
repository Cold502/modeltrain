<template>
  <div class="model-config-container">
    <!-- 页面头部 -->
    <el-card class="header-card">
      <div class="header-content">
        <div class="header-left">
      <h2>模型配置管理</h2>
        </div>
        <div class="header-actions">
          <el-button 
            type="info" 
            @click="goToPlayground"
            :icon="Monitor"
            size="default"
          >
            测试场
          </el-button>
          <el-button 
            type="primary" 
            @click="handleOpenModelDialog"
            :icon="Plus"
            size="default"
          >
        添加模型
      </el-button>
    </div>
      </div>
    </el-card>

    <!-- 模型配置列表 -->
    <div class="model-list" v-loading="loading">
      <div v-if="modelConfigList.length === 0" class="empty-state">
        <el-empty description="暂无模型配置">
          <el-button type="primary" @click="handleOpenModelDialog">
            添加第一个模型
          </el-button>
        </el-empty>
      </div>
      
      <div v-else class="model-cards">
        <el-card 
          v-for="model in modelConfigList" 
          :key="model.id" 
          class="model-card"
          :class="{ 'card-hover': true }"
          shadow="hover"
        >
          <!-- 卡片内容 -->
          <div class="card-content">
            <!-- 左侧：提供商图标和模型信息 -->
            <div class="model-info">
              <div class="provider-section">
                <ProviderIcon 
                  :provider="model.providerId" 
                  :size="32" 
                  type="color" 
                />
                <div class="model-details">
                  <h4 class="model-name">
                    {{ model.modelName || '未选择模型' }}
                  </h4>
                  <el-tag 
                    :type="getProviderTagType(model.providerId)" 
                    size="small"
                    class="provider-tag"
                  >
                    {{ model.providerName }}
                  </el-tag>
                </div>
              </div>
              
              <!-- 状态信息 -->
              <div class="status-chips">
                <el-tooltip :content="getModelStatusText(model)">
                  <el-tag 
                    :type="getModelStatusInfo(model).type"
                    size="small"
                    class="status-chip"
                  >
                    <el-icon class="chip-icon">
                      <CircleCheck v-if="getModelStatusInfo(model).success" />
                  <CircleClose v-else />
                </el-icon>
                    {{ getEndpointDisplay(model.endpoint) }}
                    {{ !model.apiKey && model.providerId?.toLowerCase() !== 'ollama' 
                        ? ' (未配置 API Key)' : '' }}
                  </el-tag>
                </el-tooltip>
                
                <el-tooltip content="模型类型提示：如果希望使用自定义视觉模型解析PDF请务必配置至少一个视觉大模型">
                  <el-tag 
                    :type="model.type === 'vision' ? 'warning' : 'info'"
                    size="small"
                    class="type-chip"
                  >
                    {{ model.type === 'vision' ? '视觉模型' : '语言模型' }}
                  </el-tag>
                </el-tooltip>
              </div>
            </div>

            <!-- 右侧：操作按钮 -->
            <div class="card-actions">
              <el-button 
                type="info" 
                :icon="Monitor" 
                size="small"
                plain
                @click="goToPlayground(model.id)"
                class="action-btn"
              >
                测试场
              </el-button>
              
              <el-button 
                type="primary" 
                :icon="Edit" 
                size="small" 
                plain
                @click="handleOpenModelDialog(model)"
                class="action-btn"
              >
                编辑
              </el-button>
              
              <el-button 
                type="danger" 
                :icon="Delete" 
                size="small" 
                plain
                @click="handleDeleteModel(model.id)"
                :disabled="modelConfigList.length <= 1"
                class="action-btn"
              >
                删除
              </el-button>
            </div>
            </div>
          </el-card>
      </div>
    </div>

    <!-- 添加/编辑模型对话框 -->
    <el-dialog 
      v-model="openModelDialog" 
      :title="editingModel ? '编辑模型配置' : '添加模型配置'"
      width="600px"
      :show-close="true"
      :close-on-click-modal="false"
      :close-on-press-escape="true"
      @close="handleCloseModelDialog"
      class="model-dialog"
    >
      <el-form 
        :model="modelConfigForm" 
        :rules="formRules" 
        ref="modelFormRef" 
        label-width="100px"
        class="model-form"
      >
        <!-- 提供商选择 -->
        <el-form-item label="提供商" prop="providerId">
              <el-select 
            v-model="modelConfigForm.providerId"
            @change="onChangeProvider"
            placeholder="选择提供商（可自定义输入）"
                filterable
                allow-create
            style="width: 100%"
              >
                <el-option
              v-for="provider in providerList"
                  :key="provider.id"
                  :label="provider.name"
                  :value="provider.id"
            >
              <div class="provider-option">
                <ProviderIcon :provider="provider.id" :size="20" />
                <span>{{ provider.name }}</span>
              </div>
            </el-option>
              </el-select>
            </el-form-item>

        <!-- 接口地址 -->
        <el-form-item label="接口地址" prop="endpoint">
          <el-input 
            v-model="modelConfigForm.endpoint" 
            placeholder="例如: https://api.openai.com/v1"
          />
        </el-form-item>

        <!-- API密钥 -->
        <el-form-item label="API密钥" prop="apiKey">
          <el-input 
            v-model="modelConfigForm.apiKey" 
            type="password" 
            placeholder="请输入您的API密钥，例如: sk-1234567890abcdefghijklmnopqrstuvwxyz"
            show-password
          />
        </el-form-item>

        <!-- 模型名称和刷新按钮 -->
        <el-form-item label="模型名称" prop="modelName">
          <div class="model-name-row">
            <el-select 
              v-model="modelConfigForm.modelName"
              @change="onModelNameChange"
                placeholder="输入或选择模型名称"
              filterable
              allow-create
              style="flex: 1"
            >
              <el-option
                v-for="model in availableModels"
                :key="model.id"
                :label="model.modelName"
                :value="model.modelName"
              />
            </el-select>
            <el-button 
              @click="refreshProviderModels" 
              :loading="refreshingModels"
              style="margin-left: 8px"
            >
                刷新模型列表
              </el-button>
          </div>
        </el-form-item>

        <!-- 模型类型 -->
        <el-form-item label="模型类型" prop="type">
          <el-select v-model="modelConfigForm.type" style="width: 100%">
            <el-option label="语言模型" value="text" />
            <el-option label="视觉模型" value="vision" />
          </el-select>
            </el-form-item>

        <!-- 模型温度 -->
        <el-form-item label="模型温度">
          <div class="slider-container">
              <el-slider 
              v-model="modelConfigForm.temperature" 
                :min="0" 
                :max="1" 
                :step="0.1"
              show-tooltip
              :format-tooltip="val => val.toString()"
              style="flex: 1"
              />
            <span class="slider-value">{{ modelConfigForm.temperature }}</span>
          </div>
            </el-form-item>

        <!-- 最大生成Token数 -->
        <el-form-item label="最大生成Token数">
          <div class="slider-container">
              <el-slider 
              v-model="modelConfigForm.maxTokens" 
              :min="1024" 
              :max="16384" 
              :step="256"
              show-tooltip
              :format-tooltip="val => val.toString()"
              style="flex: 1"
              />
            <span class="slider-value">{{ modelConfigForm.maxTokens }}</span>
          </div>
            </el-form-item>
      </el-form>

      <template #footer>
        <div class="dialog-footer">
          <el-button @click="handleCloseModelDialog">取消</el-button>
          <el-button 
            type="primary" 
            @click="handleSaveModel"
            :loading="saving"
            :disabled="!isFormValid"
          >
          保存
        </el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import { ElMessageBox } from 'element-plus'
import { message } from '@/utils/message'
import { 
  Plus, 
  Edit, 
  Delete, 
  Monitor,
  CircleCheck, 
  CircleClose 
} from '@element-plus/icons-vue'
import ProviderIcon from '@/components/ProviderIcon.vue'

export default {
  name: 'ModelConfig',
  components: {
    ProviderIcon
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    
    // 响应式数据
    const openModelDialog = ref(false)
    const editingModel = ref(null)
    const saving = ref(false)
    const refreshingModels = ref(false)
    const modelFormRef = ref()

    // 表单数据
    const modelConfigForm = reactive({
      id: '',
      providerId: '',
      providerName: '',
      endpoint: '',
      apiKey: '',
      modelId: '',
      modelName: '',
      type: 'text',
      temperature: 0.7,
      maxTokens: 8192,
      status: 1
    })

    // 表单验证规则
    const formRules = {
      providerId: [
        { required: true, message: '请选择提供商', trigger: 'change' }
      ],
      endpoint: [
        { required: true, message: '请输入接口地址', trigger: 'blur' }
      ],
      modelName: [
        { required: true, message: '请输入模型名称', trigger: 'blur' }
      ],
      type: [
        { required: true, message: '请选择模型类型', trigger: 'change' }
      ]
    }

    // 计算属性
    const modelConfigList = computed(() => store.getters['model/modelConfigList'])
    const providerList = computed(() => store.getters['model/providerList'])
    const availableModels = computed(() => store.getters['model/availableModels'])
    const loading = computed(() => store.getters['model/loading'])

    const isFormValid = computed(() => {
      return modelConfigForm.providerId && 
             modelConfigForm.providerName && 
             modelConfigForm.endpoint
    })

    // 方法
    const getProviderTagType = (providerId) => {
      const typeMap = {
        openai: 'success',
        claude: 'warning',
        ollama: 'info',
        deepseek: 'warning',
        tongyi: 'success',
        doubao: 'warning',
        kimi: 'info',
        zhipu: 'danger',
        chatglm: 'danger',
        gemini: 'success',
        wenxin: '',
        hunyuan: 'success',
        yi: 'info',
        siliconflow: 'success',
        vllm: 'info'
      }
      return typeMap[providerId] || ''
    }

    const getModelStatusInfo = (model) => {
      if (model.providerId?.toLowerCase() === 'ollama') {
        return {
          success: true,
          type: 'success',
          text: '本地模型'
        }
      } else if (model.apiKey) {
        return {
          success: true,
          type: 'success',
          text: 'API Key 已经配置'
      }
      } else {
        return {
          success: false,
          type: 'danger',
          text: 'API Key 未配置'
        }
      }
    }

    const getModelStatusText = (model) => {
      return getModelStatusInfo(model).text
    }

    const getEndpointDisplay = (endpoint) => {
      return endpoint.replace(/^https?:\/\//, '')
    }

    const handleOpenModelDialog = (model = null) => {
      console.log('🔧 打开模型对话框:', model)
      editingModel.value = model
      if (model) {
        Object.assign(modelConfigForm, model)
        if (model.providerId) {
          store.dispatch('model/fetchProviderModels', model.providerId)
        }
      } else {
        resetForm()
      }
      openModelDialog.value = true
    }

    const handleCloseModelDialog = () => {
      openModelDialog.value = false
      editingModel.value = null
      resetForm()
    }

    const resetForm = () => {
      Object.assign(modelConfigForm, {
        id: '',
        providerId: '',
        providerName: '',
        endpoint: '',
        apiKey: '',
        modelId: '',
        modelName: '',
        type: 'text',
        temperature: 0.7,
        maxTokens: 8192,
        status: 1
      })
      if (modelFormRef.value) {
        modelFormRef.value.clearValidate()
      }
    }

    const onChangeProvider = (providerId) => {
      const provider = providerList.value.find(p => p.id === providerId)
      if (provider) {
        modelConfigForm.providerName = provider.name
        modelConfigForm.endpoint = provider.apiUrl
        modelConfigForm.modelName = ''
        if (providerId) {
          store.dispatch('model/fetchProviderModels', providerId)
      }
      } else if (typeof providerId === 'string') {
        // 自定义提供商
        modelConfigForm.providerId = 'custom'
        modelConfigForm.providerName = providerId
        modelConfigForm.endpoint = ''
        modelConfigForm.modelName = ''
      }
    }

    const onModelNameChange = (modelName) => {
      const selectedModel = availableModels.value.find(m => m.modelName === modelName)
      if (selectedModel) {
        modelConfigForm.modelId = selectedModel.modelId || selectedModel.modelName
      } else {
        modelConfigForm.modelId = modelName
      }
    }

    const refreshProviderModels = async () => {
      if (!modelConfigForm.endpoint || !modelConfigForm.providerId) {
        message.warning('请先配置提供商和端点')
        return
      }

      refreshingModels.value = true
      try {
        await store.dispatch('model/refreshModels', {
          endpoint: modelConfigForm.endpoint,
          providerId: modelConfigForm.providerId,
          apiKey: modelConfigForm.apiKey
        })
        message.success('刷新成功')
      } catch (error) {
        if (error.response?.status === 401) {
          message.error('API Key 无效')
        } else {
          message.error('获取模型列表错误')
        }
      } finally {
        refreshingModels.value = false
      }
    }

    const handleSaveModel = async () => {
      if (!modelFormRef.value) return

      try {
        await modelFormRef.value.validate()
        
        // 设置modelId
        if (!modelConfigForm.modelId) {
          modelConfigForm.modelId = modelConfigForm.modelName
        }

        saving.value = true
        await store.dispatch('model/saveModelConfig', {
          config: { ...modelConfigForm },
          isEdit: !!editingModel.value
        })

        message.success(editingModel.value ? '模型配置更新成功' : '模型配置创建成功')
        handleCloseModelDialog()
        } catch (error) {
        if (error.message !== 'validation failed') {
          message.error('保存失败')
        }
        } finally {
          saving.value = false
        }
    }

    const handleDeleteModel = async (modelId) => {
      console.log('🗑️ 删除模型:', modelId)
      try {
        await ElMessageBox.confirm(
          '确认删除这个模型配置吗？', 
          '警告',
          {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
          }
        )

        await store.dispatch('model/deleteModelConfig', modelId)
        message.success('删除成功')
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除失败:', error)
          message.error('删除失败')
        }
      }
    }

    const goToPlayground = (modelId = null) => {
      console.log('🚀 跳转到测试场:', modelId)
      const query = modelId ? { modelId } : {}
      router.push({ path: '/dashboard/model-test', query })
    }

    // 初始化
    onMounted(async () => {
      console.log('🚀 ModelConfig 组件初始化')
      try {
        await Promise.all([
          store.dispatch('model/fetchProviders'),
          store.dispatch('model/fetchModelConfigs')
        ])
        console.log('✅ 初始化完成')
      } catch (error) {
        console.error('❌ 初始化失败:', error)
        message.error('初始化失败')
      }
    })

    return {
      // 图标
      Plus,
      Edit,
      Delete,
      Monitor,
      CircleCheck,
      CircleClose,
      
      // 响应式数据
      openModelDialog,
      editingModel,
      saving,
      refreshingModels,
      modelFormRef,
      modelConfigForm,
      formRules,
      
      // 计算属性
      modelConfigList,
      providerList,
      availableModels,
      loading,
      isFormValid,
      
      // 方法
      getProviderTagType,
      getModelStatusInfo,
      getModelStatusText,
      getEndpointDisplay,
      handleOpenModelDialog,
      handleCloseModelDialog,
      resetForm,
      onChangeProvider,
      onModelNameChange,
      refreshProviderModels,
      handleSaveModel,
      handleDeleteModel,
      goToPlayground
    }
  }
}
</script>

<style scoped>
.model-config-container {
  padding: 24px;
  background: var(--background-blue);
  min-height: 100vh;
  color: var(--text-color);
}

.header-card {
  margin-bottom: 24px;
  border-radius: 12px;
  background: var(--bg-color);
  border-color: var(--border-color);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0;
}

.header-left h2 {
  margin: 0;
  color: var(--text-color);
  font-weight: 600;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.model-list {
  min-height: 400px;
}

.model-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(500px, 1fr));
  gap: 20px;
}

.model-card {
  border-radius: 12px;
  background: var(--bg-color);
  border-color: var(--border-color);
  border: 1px solid var(--border-color);
}

.card-hover:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(100, 168, 219, 0.2);
}

.card-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 0;
}

.model-info {
  flex: 1;
}

.provider-section {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.model-details {
  flex: 1;
}

.model-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--text-color);
}

.provider-tag {
  font-weight: 500;
}

.status-chips {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-chip,
.type-chip {
  display: flex;
  align-items: center;
  align-self: flex-start;
}

.chip-icon {
  margin-right: 4px;
}

.card-actions {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  margin-left: 16px;
  min-width: 85px;
}

.action-btn {
  border-radius: 8px !important;
  font-weight: 500 !important;
  letter-spacing: 0.5px !important;

  width: 85px !important;
  height: 32px !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 6px !important;
  font-size: 13px !important;
  margin: 0 !important;
  padding: 0 8px !important;
  box-sizing: border-box !important;
}

.action-btn:hover {
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 12px rgba(100, 168, 219, 0.3) !important;
}

.action-btn.el-button--info.is-plain {
  color: var(--text-color) !important;
  background: var(--light-blue) !important;
  border-color: var(--border-color) !important;
}

.action-btn.el-button--info.is-plain:hover {
  background: var(--primary-blue) !important;
  border-color: var(--primary-blue) !important;
  color: #fff !important;
}

.action-btn.el-button--primary.is-plain {
  color: var(--primary-blue) !important;
  background: var(--light-blue) !important;
  border-color: var(--medium-blue) !important;
}

.action-btn.el-button--primary.is-plain:hover {
  background: var(--primary-blue) !important;
  border-color: var(--primary-blue) !important;
  color: #fff !important;
}

.action-btn.el-button--danger.is-plain {
  color: #f56c6c !important;
  background: rgba(245, 108, 108, 0.1) !important;
  border-color: rgba(245, 108, 108, 0.3) !important;
}

.action-btn.el-button--danger.is-plain:hover {
  background: #f56c6c !important;
  border-color: #f56c6c !important;
  color: #fff !important;
}

.action-btn.is-disabled {
  opacity: 0.5 !important;
  cursor: not-allowed !important;
}

.action-btn.is-disabled:hover {
  transform: none !important;
  box-shadow: none !important;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

/* 对话框样式 */
.model-dialog :deep(.el-dialog) {
  border-radius: 20px;
  box-shadow: 0 12px 48px rgba(100, 168, 219, 0.2);
  border: 2px solid var(--border-color);
  background: var(--bg-color) !important;
}

.model-dialog :deep(.el-dialog__header) {
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue)) !important;
  color: white !important;
  border-radius: 18px 18px 0 0;
  padding: 20px 24px;
}

.model-dialog :deep(.el-dialog__title) {
  color: white !important;
  font-weight: 700;
  font-size: 1.3rem;
  letter-spacing: 1px;
}

.model-dialog :deep(.el-dialog__headerbtn .el-dialog__close) {
  color: white !important;
  font-size: 18px;
}

.model-dialog :deep(.el-dialog__body) {
  padding: 24px;
  background: var(--bg-color) !important;
  color: var(--text-color) !important;
}

.model-form {
  padding: 0;
}

.model-form :deep(.el-form-item__label) {
  font-weight: 600 !important;
  color: var(--text-color) !important;
}

/* 表单特定样式 */
.model-form :deep(.el-input__wrapper) {
  border-radius: 10px !important;
}

.model-form :deep(.el-select-dropdown) {
  border-radius: 10px !important;
}

.model-form :deep(.el-textarea__inner) {
  border-radius: 10px !important;
}

.model-form :deep(.el-button) {
  border-radius: 10px !important;
  font-weight: 600;
}

.model-form :deep(.el-slider__button:hover) {
  transform: scale(1.2) !important;
}

.provider-option {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-color) !important;
}

.model-name-row {
  display: flex;
  align-items: center;
  width: 100%;
}

.slider-container {
  display: flex;
  align-items: center;
  gap: 16px;
  width: 100%;
}

.slider-value {
  min-width: 70px;
  text-align: center;
  font-weight: 600;
  color: var(--primary-blue);
  background: var(--light-blue);
  padding: 6px 16px;
  border-radius: 10px;
  border: 2px solid var(--border-color);
  font-size: 14px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px 0 0 0;
}

.dialog-footer .el-button {
  border-radius: 10px;
  padding: 10px 24px;
  font-weight: 600;
  letter-spacing: 1px;
}

.dialog-footer .el-button--primary {
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
  border: none;
}

.dialog-footer .el-button--primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(100, 168, 219, 0.4);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .model-config-container {
    padding: 16px;
  }
  
  .model-cards {
    grid-template-columns: 1fr;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .card-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .card-actions {
    flex-direction: row;
    justify-content: flex-end;
    margin-left: 0;
    gap: 6px;
  }
  
  .action-btn {
    min-width: 60px !important;
    font-size: 12px !important;
  }
}
</style> 