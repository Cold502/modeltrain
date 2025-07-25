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
              <span class="name">{{ prompt.name }}</span>
            </div>
            <div class="prompt-actions">
              <el-dropdown @command="handlePromptAction">
                <el-button text :icon="MoreFilled" />
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item :command="{ action: 'edit', prompt }">编辑</el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'validate', prompt }">验证格式</el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'convert', prompt }">格式转换</el-dropdown-item>
                    <el-dropdown-item :command="{ action: 'copy', prompt }">复制内容</el-dropdown-item>
                    <el-dropdown-item 
                      v-if="!prompt.is_system"
                      :command="{ action: 'delete', prompt }"
                      divided
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
import axios from 'axios'

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
        const response = await axios.get('/api/chat/system-prompts')
        prompts.value = response.data
      } catch (error) {
        ElMessage.error('加载提示词失败: ' + error.message)
      }
    }
    
    const loadPredefinedTemplates = async () => {
      try {
        const response = await axios.get('/api/chat/system-prompts/predefined')
        predefinedTemplates.value = response.data.prompts
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
          await axios.post('/api/chat/system-prompts', promptForm)
          ElMessage.success('创建成功')
        } else {
          await axios.put(`/api/chat/system-prompts/${promptForm.id}`, promptForm)
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
        await axios.post(`/api/chat/system-prompts/predefined/${template.key}`)
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
          `确定要删除提示词 "${prompt.name}" 吗？`,
          '确认删除',
          { type: 'warning' }
        )
        
        await axios.delete(`/api/chat/system-prompts/${prompt.id}`)
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
        const response = await axios.post('/api/chat/system-prompts/convert', {
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
        const response = await axios.post(`/api/chat/system-prompts/${promptId}/validate`)
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
        const response = await axios.post('/api/chat/system-prompts/convert', convertForm)
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
      copyConvertResult
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
</style> 