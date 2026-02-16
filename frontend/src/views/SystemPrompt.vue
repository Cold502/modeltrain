<template>
  <div class="page-container">
    <div class="header-section">
      <h2 class="page-title">
        <el-icon><ChatLineSquare /></el-icon>
        系统提示词管理
      </h2>
      <p class="page-description">创建和管理OpenAI、Ollama等格式的系统提示词</p>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="filters">
        <el-select v-model="filters.category" placeholder="选择分类" clearable style="width: 150px;">
          <el-option v-for="cat in categories" :key="cat" :label="getCategoryLabel(cat)" :value="cat" />
        </el-select>
        <el-select v-model="filters.format" placeholder="选择格式" clearable style="width: 150px;">
          <el-option v-for="fmt in formats" :key="fmt" :label="getFormatLabel(fmt)" :value="fmt" />
        </el-select>
        <el-button @click="loadPrompts" :icon="Refresh">刷新</el-button>
      </div>
      <div class="actions">
        <el-button type="primary" @click="showCreateDialog" :icon="Plus">创建提示词</el-button>
        <el-button @click="showPredefinedDialog" :icon="Collection">预定义模板</el-button>
      </div>
    </div>

    <!-- 提示词列表 -->
    <div class="prompts-grid">
      <el-card 
        v-for="prompt in filteredPrompts" 
        :key="prompt.id" 
        class="prompt-card"
        shadow="hover"
      >
        <template #header>
          <div class="card-header">
            <div class="prompt-title">
              <el-tag v-if="prompt.is_default" type="success" size="small">默认</el-tag>
              <el-tag v-if="prompt.is_system" type="info" size="small">系统</el-tag>
              <el-tag v-if="!prompt.is_system && prompt.name !== '系统通用助手'" type="warning" size="small" class="deletable-tag">可删除</el-tag>
              <span class="name">{{ prompt.name }}</span>
            </div>
            <div class="prompt-actions">
              <el-dropdown @command="handlePromptAction">
                <el-button text :icon="MoreFilled" class="action-button" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{ action: 'edit', prompt }">编辑</el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'validate', prompt }">验证格式</el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'convert', prompt }">格式转换</el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'copy', prompt }">复制内容</el-dropdown-item>
                    <el-dropdown-item 
                      v-if="!prompt.is_system && prompt.name !== '系统通用助手'"
                      :command="{ action: 'delete', prompt }"
                      divided
                      style="color: #f56c6c; background-color: #fef0f0; border-left: 3px solid #f56c6c; margin: 4px 0; border-radius: 4px;"
                    >删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </div>
        </template>
        
        <div class="prompt-content">
          <div class="prompt-meta">
            <el-tag type="primary" size="small">{{ getFormatLabel(prompt.format_type) }}</el-tag>
            <el-tag size="small">{{ getCategoryLabel(prompt.category) }}</el-tag>
            <span class="create-time">{{ formatTime(prompt.created_at) }}</span>
          </div>
          
          <div class="prompt-description" v-if="prompt.description">
            {{ prompt.description }}
          </div>
          
          <div class="prompt-preview">
            {{ truncateText(prompt.content, 200) }}
          </div>
        </div>
      </el-card>
    </div>

    <!-- 空状态 -->
    <el-empty v-if="filteredPrompts.length === 0" description="暂无系统提示词">
      <el-button type="primary" @click="showCreateDialog">创建第一个提示词</el-button>
    </el-empty>

    <!-- 创建/编辑对话框 -->
    <el-dialog 
      v-model="dialogVisible" 
      :title="dialogMode === 'create' ? '创建系统提示词' : '编辑系统提示词'"
      width="70%"
      :close-on-click-modal="false"
    >
      <el-form ref="promptFormRef" :model="promptForm" :rules="promptRules" label-width="100px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="名称" prop="name">
              <el-input v-model="promptForm.name" placeholder="请输入提示词名称" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="分类" prop="category">
              <el-select v-model="promptForm.category" placeholder="选择分类">
                <el-option v-for="cat in categories" :key="cat" :label="getCategoryLabel(cat)" :value="cat" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="格式类型" prop="format_type">
              <el-select v-model="promptForm.format_type" placeholder="选择格式">
                <el-option v-for="fmt in formats" :key="fmt" :label="getFormatLabel(fmt)" :value="fmt" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="设为默认">
              <el-switch v-model="promptForm.is_default" />
            </el-form-item>
          </el-col>
        </el-row>
        
        <el-form-item label="描述">
          <el-input 
            v-model="promptForm.description" 
            type="textarea" 
            :rows="2"
            placeholder="请输入提示词描述（可选）"
          />
        </el-form-item>
        
        <el-form-item label="提示词内容" prop="content">
          <el-input 
            v-model="promptForm.content"
            type="textarea"
            :rows="8"
            placeholder="请输入系统提示词内容"
            show-word-limit
            maxlength="10000"
          />
          <div class="content-tips">
            <el-text size="small" type="info">
              <el-icon><InfoFilled /></el-icon>
              {{ getFormatTips(promptForm.format_type) }}
            </el-text>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <div class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button @click="validateCurrentPrompt" :icon="Check">验证格式</el-button>
          <el-button type="primary" @click="savePrompt" :loading="saving">
            {{ dialogMode === 'create' ? '创建' : '保存' }}
          </el-button>
        </div>
      </template>
    </el-dialog>

    <!-- 预定义模板对话框 -->
    <el-dialog v-model="predefinedDialogVisible" title="预定义提示词模板" width="80%">
      <div class="predefined-grid">
        <el-card 
          v-for="template in predefinedTemplates" 
          :key="template.key"
          class="template-card"
          shadow="hover"
          @click="selectTemplate(template)"
        >
          <div class="template-header">
            <h4>{{ template.name }}</h4>
            <el-tag>{{ getFormatLabel(template.format_type) }}</el-tag>
          </div>
          <p class="template-description">{{ template.description }}</p>
          <div class="template-content">{{ truncateText(template.content, 150) }}</div>
        </el-card>
      </div>
    </el-dialog>

    <!-- 格式转换对话框 -->
    <el-dialog v-model="convertDialogVisible" title="格式转换" width="60%">
      <el-form>
        <el-form-item label="源格式">
          <el-select v-model="convertForm.source_format">
            <el-option v-for="fmt in formats" :key="fmt" :label="getFormatLabel(fmt)" :value="fmt" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="目标格式">
          <el-select v-model="convertForm.target_format">
            <el-option v-for="fmt in formats" :key="fmt" :label="getFormatLabel(fmt)" :value="fmt" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="原始内容">
          <el-input 
            v-model="convertForm.content"
            type="textarea"
            :rows="4"
            readonly
          />
        </el-form-item>
        
        <el-form-item label="转换结果" v-if="convertResult">
          <el-input 
            v-model="convertResult.converted_content"
            type="textarea"
            :rows="6"
            readonly
          />
          <div class="convert-info" v-if="convertResult.format_info">
            <el-text size="small">
              变更说明: {{ Array.isArray(convertResult.format_info.changes) ? 
                convertResult.format_info.changes.join(', ') : 
                convertResult.format_info.changes }}
            </el-text>
          </div>
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="convertDialogVisible = false">关闭</el-button>
        <el-button type="primary" @click="performConvert" :loading="converting">转换</el-button>
        <el-button v-if="convertResult" @click="copyConvertResult" :icon="CopyDocument">复制结果</el-button>
      </template>
    </el-dialog>

    <!-- 验证结果对话框 -->
    <el-dialog v-model="validationDialogVisible" title="格式验证结果" width="70%">
      <div v-if="validationResult">
        <el-alert 
          :type="validationResult.validation.is_valid ? 'success' : 'error'"
          :title="validationResult.validation.is_valid ? '格式验证通过' : '格式验证失败'"
          show-icon
          :closable="false"
        />
        
        <div v-if="validationResult.validation.errors.length > 0" class="validation-section">
          <h4>错误信息:</h4>
          <ul>
            <li v-for="error in validationResult.validation.errors" :key="error" class="error-item">
              {{ error }}
            </li>
          </ul>
        </div>
        
        <div v-if="validationResult.validation.warnings.length > 0" class="validation-section">
          <h4>警告信息:</h4>
          <ul>
            <li v-for="warning in validationResult.validation.warnings" :key="warning" class="warning-item">
              {{ warning }}
            </li>
      </ul>
        </div>
        
        <div v-if="validationResult.examples" class="validation-section">
          <h4>使用示例:</h4>
          <el-tabs>
            <el-tab-pane v-for="(example, key) in validationResult.examples" :key="key" :label="key">
              <pre><code>{{ typeof example === 'object' ? JSON.stringify(example, null, 2) : example }}</code></pre>
            </el-tab-pane>
          </el-tabs>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  ChatLineSquare, Plus, Collection, Refresh, MoreFilled, 
  Check, InfoFilled, CopyDocument 
} from '@element-plus/icons-vue'
import api, { chatAPI } from '@/utils/api'

export default {
  name: 'SystemPrompt',
  components: {
    ChatLineSquare, Plus, Collection, Refresh, MoreFilled,
    Check, InfoFilled, CopyDocument
  },
  setup() {
    const prompts = ref([])
    const predefinedTemplates = ref([])
    const dialogVisible = ref(false)
    const predefinedDialogVisible = ref(false)
    const convertDialogVisible = ref(false)
    const validationDialogVisible = ref(false)
    const dialogMode = ref('create')
    const saving = ref(false)
    const converting = ref(false)
    const promptFormRef = ref()
    
    const categories = ['general', 'coding', 'translation', 'creative', 'academic', 'business']
    const formats = ['openai', 'ollama', 'custom']
    
    const filters = reactive({
      category: '',
      format: ''
    })
    
    const promptForm = reactive({
      name: '',
      content: '',
      description: '',
      format_type: 'openai',
      category: 'general',
      is_default: false
    })
    
    const convertForm = reactive({
      content: '',
      source_format: 'openai',
      target_format: 'ollama'
    })
    
    const convertResult = ref(null)
    const validationResult = ref(null)
    
    const promptRules = {
      name: [{ required: true, message: '请输入提示词名称', trigger: 'blur' }],
      content: [{ required: true, message: '请输入提示词内容', trigger: 'blur' }],
      format_type: [{ required: true, message: '请选择格式类型', trigger: 'change' }],
      category: [{ required: true, message: '请选择分类', trigger: 'change' }]
    }
    
    const filteredPrompts = computed(() => {
      return prompts.value.filter(prompt => {
        if (filters.category && prompt.category !== filters.category) return false
        if (filters.format && prompt.format_type !== filters.format) return false
        return true
      })
    })
    
    const getCategoryLabel = (category) => {
      const labels = {
        general: '通用',
        coding: '编程',
        translation: '翻译',
        creative: '创意',
        academic: '学术',
        business: '商业'
      }
      return labels[category] || category
    }
    
    const getFormatLabel = (format) => {
      const labels = {
        openai: 'OpenAI',
        ollama: 'Ollama',
        custom: '自定义'
      }
      return labels[format] || format
    }
    
    const getFormatTips = (format) => {
      const tips = {
        openai: 'OpenAI格式: 直接输入提示词文本，将作为system消息使用',
        ollama: 'Ollama格式: 可使用模板语法，如 {{ .System }}、{{ .Content }} 等',
        custom: '自定义格式: 可以使用任意格式，支持模板变量和特殊标记'
      }
      return tips[format] || '请输入符合所选格式的提示词内容'
    }
    
    const truncateText = (text, length) => {
      if (!text) return ''
      return text.length > length ? text.substring(0, length) + '...' : text
    }
    
    const formatTime = (time) => {
      return new Date(time).toLocaleString('zh-CN')
    }
    
    const loadPrompts = async () => {
      try {
        const response = await chatAPI.getSystemPrompts()
        console.log('系统提示词响应:', response.data)
        // 确保prompts是数组
        if (Array.isArray(response.data)) {
          prompts.value = response.data
        } else {
          console.error('返回数据不是数组:', response.data)
          prompts.value = []
          ElMessage.error('数据格式错误')
        }
      } catch (error) {
        console.error('加载提示词失败:', error)
        ElMessage.error('加载提示词失败: ' + error.message)
        prompts.value = []
      }
    }
    
    const loadPredefinedTemplates = async () => {
      try {
        const response = await chatAPI.getSystemPrompts()
        console.log('预定义模板响应:', response.data)
        predefinedTemplates.value = response.data.prompts || []
      } catch (error) {
        ElMessage.error('加载预定义模板失败: ' + error.message)
      }
    }
    
    const showCreateDialog = () => {
      dialogMode.value = 'create'
      resetForm()
      dialogVisible.value = true
    }
    
    const showEditDialog = (prompt) => {
      dialogMode.value = 'edit'
      Object.assign(promptForm, {
        id: prompt.id,
        name: prompt.name,
        content: prompt.content,
        description: prompt.description || '',
        format_type: prompt.format_type,
        category: prompt.category,
        is_default: prompt.is_default
      })
      dialogVisible.value = true
    }
    
    const showPredefinedDialog = () => {
      loadPredefinedTemplates()
      predefinedDialogVisible.value = true
    }
    
    const resetForm = () => {
      Object.assign(promptForm, {
        id: null,
        name: '',
        content: '',
        description: '',
        format_type: 'openai',
        category: 'general',
        is_default: false
      })
    }
    
    const savePrompt = async () => {
      if (!promptFormRef.value) return
      
      try {
        await promptFormRef.value.validate()
        saving.value = true
        
        if (dialogMode.value === 'create') {
          await chatAPI.createSystemPrompt(promptForm)
          ElMessage.success('创建成功')
        } else {
          await chatAPI.updateSystemPrompt(promptForm.id, promptForm)
          ElMessage.success('更新成功')
        }
        
        dialogVisible.value = false
        loadPrompts()
      } catch (error) {
        ElMessage.error('保存失败: ' + error.message)
      } finally {
        saving.value = false
      }
    }
    
    const selectTemplate = async (template) => {
      try {
        await chatAPI.createSystemPrompt(template)
        ElMessage.success('模板添加成功')
        predefinedDialogVisible.value = false
        loadPrompts()
      } catch (error) {
        ElMessage.error('添加模板失败: ' + error.message)
      }
    }
    
    const handlePromptAction = async ({ action, prompt }) => {
      switch (action) {
        case 'edit':
          showEditDialog(prompt)
          break
        case 'validate':
          await validatePrompt(prompt.id)
          break
        case 'convert':
          showConvertDialog(prompt)
          break
        case 'copy':
          await copyToClipboard(prompt.content)
          break
        case 'delete':
          await deletePrompt(prompt)
          break
      }
    }
    
    const deletePrompt = async (prompt) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除提示词 "${prompt.name}" 吗？\n\n删除后将无法恢复，请谨慎操作。`,
          '确认删除',
          { 
            type: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消',
            dangerouslyUseHTMLString: false
          }
        )
        
        await chatAPI.deleteSystemPrompt(prompt.id)
        ElMessage.success('删除成功')
        loadPrompts()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除失败: ' + error.message)
        }
      }
    }
    
    const validateCurrentPrompt = async () => {
      if (!promptForm.content) {
        ElMessage.warning('请先输入提示词内容')
        return
      }
      
      try {
        const response = await api.post('/chat/system-prompts/convert', {
          content: promptForm.content,
          source_format: promptForm.format_type,
          target_format: promptForm.format_type
        })
        
        if (response.data.format_info.changes === '无变化') {
          ElMessage.success('格式验证通过')
        } else {
          ElMessage.info('格式已优化: ' + response.data.format_info.changes.join(', '))
        }
      } catch (error) {
        ElMessage.error('验证失败: ' + error.message)
      }
    }
    
    const validatePrompt = async (promptId) => {
      try {
        const response = await api.post(`/chat/system-prompts/${promptId}/validate`)
        validationResult.value = response.data
        validationDialogVisible.value = true
      } catch (error) {
        ElMessage.error('验证失败: ' + error.message)
      }
    }
    
    const showConvertDialog = (prompt) => {
      convertForm.content = prompt.content
      convertForm.source_format = prompt.format_type
      convertForm.target_format = prompt.format_type === 'openai' ? 'ollama' : 'openai'
      convertResult.value = null
      convertDialogVisible.value = true
    }
    
    const performConvert = async () => {
      try {
        converting.value = true
        const response = await api.post('/chat/system-prompts/convert', convertForm)
        convertResult.value = response.data
      } catch (error) {
        ElMessage.error('转换失败: ' + error.message)
      } finally {
        converting.value = false
      }
    }
    
    const copyConvertResult = async () => {
      if (convertResult.value) {
        await copyToClipboard(convertResult.value.converted_content)
      }
    }
    
    const copyToClipboard = async (text) => {
      try {
        await navigator.clipboard.writeText(text)
        ElMessage.success('已复制到剪贴板')
      } catch (error) {
        ElMessage.error('复制失败')
      }
    }
    
    onMounted(() => {
      loadPrompts()
    })
    
    return {
      prompts,
      predefinedTemplates,
      dialogVisible,
      predefinedDialogVisible,
      convertDialogVisible,
      validationDialogVisible,
      dialogMode,
      saving,
      converting,
      promptFormRef,
      categories,
      formats,
      filters,
      promptForm,
      convertForm,
      convertResult,
      validationResult,
      promptRules,
      filteredPrompts,
      getCategoryLabel,
      getFormatLabel,
      getFormatTips,
      truncateText,
      formatTime,
      loadPrompts,
      showCreateDialog,
      showPredefinedDialog,
      savePrompt,
      selectTemplate,
      handlePromptAction,
      validateCurrentPrompt,
      performConvert,
      copyConvertResult,
      ChatLineSquare,
      Plus,
      Collection,
      Refresh,
      MoreFilled,
      Check,
      InfoFilled,
      CopyDocument
    }
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header-section {
  margin-bottom: 30px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 10px 0;
  color: var(--el-text-color-primary);
}

.page-description {
  color: var(--el-text-color-regular);
  margin: 0;
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding: 15px;
  background: var(--el-bg-color-page);
  border-radius: 8px;
}

.filters {
  display: flex;
  gap: 10px;
  align-items: center;
}

.actions {
  display: flex;
  gap: 10px;
}

.prompts-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.prompt-card {
  transition: transform 0.2s;
}

.prompt-card:hover {
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.prompt-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.prompt-title .name {
  font-weight: bold;
  color: var(--el-text-color-primary);
}

.prompt-content {
  color: var(--el-text-color-regular);
}

.prompt-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}

.create-time {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  margin-left: auto;
}

.prompt-description {
  font-size: 14px;
  color: var(--el-text-color-regular);
  margin-bottom: 10px;
  font-style: italic;
}

.prompt-preview {
  font-size: 13px;
  line-height: 1.4;
  background: var(--el-fill-color-light);
  padding: 10px;
  border-radius: 4px;
  border-left: 3px solid var(--el-color-primary);
}

.content-tips {
  margin-top: 5px;
}

.predefined-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 15px;
}

.template-card {
  cursor: pointer;
  transition: all 0.2s;
}

.template-card:hover {
  border-color: var(--el-color-primary);
  transform: translateY(-2px);
}

.template-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.template-header h4 {
  margin: 0;
  color: var(--el-text-color-primary);
}

.template-description {
  color: var(--el-text-color-regular);
  font-size: 13px;
  margin-bottom: 10px;
}

.template-content {
  font-size: 12px;
  color: var(--el-text-color-placeholder);
  background: var(--el-fill-color-light);
  padding: 8px;
  border-radius: 4px;
  max-height: 60px;
  overflow: hidden;
}

.validation-section {
  margin: 15px 0;
}

.validation-section h4 {
  margin: 0 0 10px 0;
  color: var(--el-text-color-primary);
}

.validation-section ul {
  margin: 0;
  padding-left: 20px;
}

.error-item {
  color: var(--el-color-danger);
}

.warning-item {
  color: var(--el-color-warning);
}

.convert-info {
  margin-top: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

pre {
  background: var(--el-fill-color-light);
  padding: 15px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 13px;
  line-height: 1.4;
}

.prompt-actions {
  display: flex;
  align-items: center;
}

.prompt-actions .el-button {
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.prompt-actions .el-button:hover {
  background-color: var(--el-fill-color-light);
  color: var(--el-color-primary) !important;
}

.prompt-actions .el-dropdown {
  display: block;
}

/* 新增的样式 */
.action-button {
  color: #606266 !important;
  font-size: 16px !important;
  padding: 8px !important;
  border-radius: 6px !important;
  transition: all 0.3s ease !important;
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%) !important;
  border: 1px solid #e4e7ed !important;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1) !important;
}

.action-button:hover {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
  color: white !important;
  transform: translateY(-1px) !important;
  box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3) !important;
}

/* 下拉菜单样式优化 */
.prompt-actions .el-dropdown-menu {
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
  border: 1px solid #e4e7ed !important;
}

.prompt-actions .el-dropdown-menu .el-dropdown-item {
  padding: 10px 16px !important;
  transition: all 0.2s ease !important;
}

.prompt-actions .el-dropdown-menu .el-dropdown-item:hover {
  background-color: #f5f7fa !important;
  color: var(--el-color-primary) !important;
}

/* 删除按钮特殊样式 */
.prompt-actions .el-dropdown-menu .el-dropdown-item[style*="color: #f56c6c"] {
  position: relative !important;
  overflow: hidden !important;
}

.prompt-actions .el-dropdown-menu .el-dropdown-item[style*="color: #f56c6c"]:hover {
  background: linear-gradient(135deg, #fef0f0 0%, #fde2e2 100%) !important;
  color: #f56c6c !important;
  transform: translateX(2px) !important;
  box-shadow: 0 2px 8px rgba(245, 108, 108, 0.2) !important;
}

/* 可删除标签样式 */
.deletable-tag {
  background: linear-gradient(135deg, #ff9a9e 0%, #fecfef 50%, #fecfef 100%) !important;
  color: #d63384 !important;
  border: 1px solid #ff9a9e !important;
  font-weight: bold !important;
  animation: pulse 2s infinite !important;
  box-shadow: 0 2px 4px rgba(255, 154, 158, 0.3) !important;
}

.deletable-tag:hover {
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8e8e 50%, #ff8e8e 100%) !important;
  transform: scale(1.05) !important;
  box-shadow: 0 4px 8px rgba(255, 107, 107, 0.4) !important;
}

@keyframes pulse {
  0% {
    box-shadow: 0 2px 4px rgba(255, 154, 158, 0.3);
  }
  50% {
    box-shadow: 0 2px 8px rgba(255, 154, 158, 0.5);
  }
  100% {
    box-shadow: 0 2px 4px rgba(255, 154, 158, 0.3);
  }
}
</style>

<style>
/* 暗色模式样式（非 scoped） */
.dark-mode .page-container {
  background: transparent;
  color: #e4e9f5;
}

.dark-mode .page-title {
  color: #f4f6ff !important;
}

.dark-mode .page-description {
  color: #c0cae5 !important;
}

.dark-mode .action-bar {
  background: #151b2c !important;
  border: 1px solid #2a3550;
}

.dark-mode .prompt-card,
.dark-mode .template-card {
  background: #151b2c !important;
  border-color: #2a3550 !important;
}

.dark-mode .prompt-card:hover,
.dark-mode .template-card:hover {
  border-color: #4a7afe !important;
  box-shadow: 0 4px 12px rgba(74, 122, 254, 0.2) !important;
}

.dark-mode .card-header {
  border-bottom-color: #2a3550 !important;
}

.dark-mode .prompt-title .name,
.dark-mode .template-header h4 {
  color: #f4f6ff !important;
}

.dark-mode .prompt-content,
.dark-mode .prompt-description,
.dark-mode .template-description {
  color: #c0cae5 !important;
}

.dark-mode .prompt-preview,
.dark-mode .template-content {
  background: rgba(26, 34, 52, 0.6) !important;
  color: #b8c5e0 !important;
  border-left-color: #4a7afe !important;
}

.dark-mode .create-time {
  color: #7a8aa3 !important;
}

.dark-mode .action-button {
  background: linear-gradient(135deg, #1a2234 0%, #2a3550 100%) !important;
  border-color: #3a4560 !important;
  color: #e4e9f5 !important;
}

.dark-mode .action-button:hover {
  background: linear-gradient(135deg, #4a7afe 0%, #6b8fff 100%) !important;
  color: #ffffff !important;
}

/* Dialog 暗色模式 */
.dark-mode .el-dialog {
  background: #151b2c !important;
  border: 1px solid #2a3550 !important;
}

.dark-mode .el-dialog__header {
  background: transparent !important;
  border-bottom: 1px solid #2a3550 !important;
}

.dark-mode .el-dialog__title {
  color: #f4f6ff !important;
}

.dark-mode .el-dialog__body {
  background: transparent !important;
  color: #e4e9f5 !important;
}

.dark-mode .el-form-item__label {
  color: #c0cae5 !important;
}

.dark-mode .el-input__wrapper {
  background: #0f1522 !important;
  border-color: #273554 !important;
  box-shadow: none !important;
}

.dark-mode .el-input__inner,
.dark-mode .el-textarea__inner {
  background: transparent !important;
  color: #e4e9f5 !important;
}

.dark-mode .el-select__wrapper {
  background: #0f1522 !important;
  border-color: #273554 !important;
  box-shadow: none !important;
}

.dark-mode .el-dialog__footer {
  background: transparent !important;
  border-top: 1px solid #2a3550 !important;
}

.dark-mode .el-button {
  background: #1a2234 !important;
  border-color: #2a3550 !important;
  color: #e4e9f5 !important;
}

.dark-mode .el-button:hover {
  background: #243249 !important;
  border-color: #3a4560 !important;
}

.dark-mode .el-button--primary {
  background: var(--el-color-primary) !important;
  border-color: var(--el-color-primary) !important;
  color: #fff !important;
}

.dark-mode .el-empty__description {
  color: #b8c1da !important;
}

.dark-mode pre {
  background: #1a2234 !important;
  color: #e4e9f5 !important;
  border: 1px solid #2a3550;
}

.dark-mode .content-tips .el-text {
  color: #a8b5d1 !important;
}

.dark-mode .convert-info .el-text {
  color: #a8b5d1 !important;
}

.dark-mode .el-alert {
  background: #1a2234 !important;
  border-color: #2a3550 !important;
}

.dark-mode .el-alert--success {
  background: rgba(103, 194, 58, 0.1) !important;
  border-color: rgba(103, 194, 58, 0.3) !important;
  color: #67c23a !important;
}

.dark-mode .el-alert--error {
  background: rgba(245, 108, 108, 0.1) !important;
  border-color: rgba(245, 108, 108, 0.3) !important;
  color: #f56c6c !important;
}

.dark-mode .validation-section h4 {
  color: #f4f6ff !important;
}

.dark-mode .error-item {
  color: #f88 !important;
}

.dark-mode .warning-item {
  color: #fa6 !important;
}

/* 下拉菜单暗色模式 */
.dark-mode .el-dropdown-menu {
  background: #151b2c !important;
  border-color: #2a3550 !important;
}

.dark-mode .el-dropdown-menu__item {
  color: #e4e9f5 !important;
}

.dark-mode .el-dropdown-menu__item:hover {
  background: #1a2234 !important;
  color: #4a7afe !important;
}

/* Select 下拉菜单 */
.dark-mode .el-select-dropdown {
  background: #151b2c !important;
  border-color: #2a3550 !important;
}

.dark-mode .el-select-dropdown__item {
  color: #e4e9f5 !important;
}

.dark-mode .el-select-dropdown__item:hover,
.dark-mode .el-select-dropdown__item.is-selected {
  background: #1a2234 !important;
  color: #4a7afe !important;
}

/* Tabs 暗色模式 */
.dark-mode .el-tabs__header {
  background: transparent !important;
}

.dark-mode .el-tabs__nav {
  background: transparent !important;
}

.dark-mode .el-tabs__item {
  color: #c0cae5 !important;
}

.dark-mode .el-tabs__item:hover,
.dark-mode .el-tabs__item.is-active {
  color: #4a7afe !important;
}

.dark-mode .el-tabs__active-bar {
  background-color: #4a7afe !important;
}

/* Tag 暗色模式 */
.dark-mode .el-tag {
  background: rgba(58, 122, 254, 0.2) !important;
  border-color: rgba(58, 122, 254, 0.4) !important;
  color: #a7c8ff !important;
}

.dark-mode .el-tag--success {
  background: rgba(103, 194, 58, 0.2) !important;
  border-color: rgba(103, 194, 58, 0.4) !important;
  color: #95d475 !important;
}

.dark-mode .el-tag--info {
  background: rgba(100, 116, 139, 0.2) !important;
  border-color: rgba(100, 116, 139, 0.4) !important;
  color: #94a3b8 !important;
}

.dark-mode .el-tag--warning {
  background: rgba(230, 162, 60, 0.2) !important;
  border-color: rgba(230, 162, 60, 0.4) !important;
  color: #f0a020 !important;
}

/* Switch 暗色模式 */
.dark-mode .el-switch__core {
  background: #2a3550 !important;
  border-color: #3a4560 !important;
}

.dark-mode .el-switch.is-checked .el-switch__core {
  background: var(--el-color-primary) !important;
}
</style>