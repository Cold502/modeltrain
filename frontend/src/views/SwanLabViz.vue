<template>
  <div class="page-container">
    <h2>训练可视化 - SwanLab</h2>
    <p>查看模型训练过程和结果的可视化图表</p>
    
    <!-- SwanLab 状态和配置 -->
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>SwanLab 服务状态</span>
          <div>
            <el-button 
              type="primary" 
              @click="openSwanLab"
              :disabled="!swanlabInfo.status"
              style="margin-right: 10px;"
            >
              打开 SwanLab
            </el-button>
            <el-button 
              type="success" 
              @click="startSwanLab"
              :loading="startingSwanLab"
              :disabled="swanlabInfo.status === 'running'"
            >
              启动 SwanLab
            </el-button>
          </div>
        </div>
      </template>
      
      <!-- SwanLab 状态显示 -->
      <div class="swanlab-status">
        <el-row :gutter="20">
          <el-col :span="8">
            <div class="status-card">
              <div class="status-icon" :class="swanlabInfo.status">
                <el-icon size="24">
                  <component :is="getStatusIcon(swanlabInfo.status)" />
                </el-icon>
              </div>
              <div class="status-info">
                <h4>服务状态</h4>
                <p>{{ getStatusText(swanlabInfo.status) }}</p>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="status-card">
              <div class="status-icon">
                <el-icon size="24"><Link /></el-icon>
              </div>
              <div class="status-info">
                <h4>访问地址</h4>
                <p>{{ swanlabInfo.url || '未配置' }}</p>
              </div>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="status-card">
              <div class="status-icon">
                <el-icon size="24"><FolderOpened /></el-icon>
              </div>
              <div class="status-info">
                <h4>项目数量</h4>
                <p>{{ swanlabInfo.projects?.length || 0 }} 个</p>
              </div>
            </div>
          </el-col>
        </el-row>
      </div>

      <!-- SwanLab 配置 -->
      <el-divider />
      <div class="swanlab-config">
        <h4>SwanLab 配置</h4>
        <el-form :model="swanlabConfig" label-width="120px" size="small">
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="服务地址">
                <el-input 
                  v-model="swanlabConfig.host" 
                  placeholder="localhost"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="端口">
                <el-input-number 
                  v-model="swanlabConfig.port" 
                  :min="1000" 
                  :max="9999"
                  placeholder="5092"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="数据目录">
                <el-input 
                  v-model="swanlabConfig.data_dir" 
                  placeholder="/path/to/swanlab/data"
                />
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="项目名称">
                <el-input 
                  v-model="swanlabConfig.project_name" 
                  placeholder="modeltrain"
                />
              </el-form-item>
            </el-col>
          </el-row>
          <el-form-item>
            <el-button type="primary" @click="saveConfig" :loading="savingConfig">
              保存配置
            </el-button>
            <el-button @click="testConnection" :loading="testingConnection">
              测试连接
            </el-button>
          </el-form-item>
        </el-form>
      </div>
    </el-card>

    <!-- 训练项目列表 -->
    <el-card>
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>训练项目</span>
          <div>
            <el-button @click="refreshProjects" :loading="loadingProjects">
              刷新
            </el-button>
            <el-button type="primary" @click="createProject">
              新建项目
            </el-button>
          </div>
        </div>
      </template>
      
      <div v-if="loadingProjects" class="loading-container">
        <el-skeleton :rows="3" animated />
      </div>
      
      <div v-else-if="swanlabInfo.projects && swanlabInfo.projects.length > 0" class="projects-grid">
        <el-card 
          v-for="project in swanlabInfo.projects" 
          :key="project.name"
          class="project-card"
          shadow="hover"
        >
          <template #header>
            <div class="project-header">
              <span class="project-name">{{ project.name }}</span>
              <el-tag :type="getProjectStatusType(project.status)" size="small">
                {{ project.status }}
              </el-tag>
            </div>
          </template>
          
          <div class="project-content">
            <p><strong>创建时间:</strong> {{ formatTime(project.created_at) }}</p>
            <p><strong>实验数量:</strong> {{ project.experiments?.length || 0 }}</p>
            <p><strong>最后更新:</strong> {{ formatTime(project.updated_at) }}</p>
          </div>
          
          <div class="project-actions">
            <el-button 
              type="primary" 
              size="small" 
              @click="openProject(project)"
            >
              查看详情
            </el-button>
            <el-button 
              type="danger" 
              size="small" 
              @click="deleteProject(project)"
            >
              删除
            </el-button>
          </div>
        </el-card>
      </div>
      
      <el-empty v-else description="暂无训练项目" />
    </el-card>

    <!-- 新建项目对话框 -->
    <el-dialog 
      v-model="showCreateDialog" 
      title="新建训练项目" 
      width="500px"
    >
      <el-form :model="newProject" label-width="100px">
        <el-form-item label="项目名称" required>
          <el-input v-model="newProject.name" placeholder="输入项目名称" />
        </el-form-item>
        <el-form-item label="项目描述">
          <el-input 
            v-model="newProject.description" 
            type="textarea" 
            :rows="3"
            placeholder="输入项目描述"
          />
        </el-form-item>
      </el-form>
      
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" @click="confirmCreateProject" :loading="creatingProject">
          创建
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script>
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { 
  Link, 
  FolderOpened, 
  CircleCheck, 
  CircleClose, 
  Loading,
  Warning
} from '@element-plus/icons-vue'
import { trainingAPI } from '@/utils/api'

export default {
  name: 'SwanLabViz',
  components: {
    Link,
    FolderOpened,
    CircleCheck,
    CircleClose,
    Loading,
    Warning
  },
  setup() {
    const swanlabInfo = ref({
      status: 'unknown',
      url: '',
      projects: []
    })
    
    const swanlabConfig = reactive({
      host: 'localhost',
      port: 5092,
      data_dir: './swanlab_data',
      project_name: 'modeltrain'
    })
    
    const loadingProjects = ref(false)
    const startingSwanLab = ref(false)
    const savingConfig = ref(false)
    const testingConnection = ref(false)
    const creatingProject = ref(false)
    const showCreateDialog = ref(false)
    
    const newProject = reactive({
      name: '',
      description: ''
    })

    // 获取状态图标
    const getStatusIcon = (status) => {
      switch (status) {
        case 'running':
          return 'CircleCheck'
        case 'stopped':
          return 'CircleClose'
        case 'starting':
          return 'Loading'
        case 'error':
          return 'Warning'
        default:
          return 'CircleClose'
      }
    }

    // 获取状态文本
    const getStatusText = (status) => {
      switch (status) {
        case 'running':
          return '运行中'
        case 'stopped':
          return '已停止'
        case 'starting':
          return '启动中'
        case 'error':
          return '错误'
        default:
          return '未知'
      }
    }

    // 获取项目状态类型
    const getProjectStatusType = (status) => {
      switch (status) {
        case 'active':
          return 'success'
        case 'completed':
          return 'info'
        case 'failed':
          return 'danger'
        default:
          return 'warning'
      }
    }

    // 格式化时间
    const formatTime = (timeStr) => {
      if (!timeStr) return '未知'
      const date = new Date(timeStr)
      return date.toLocaleString('zh-CN')
    }

    // 加载 SwanLab 信息
    const loadSwanLabInfo = async () => {
      try {
        const response = await trainingAPI.getSwanLabInfo()
        swanlabInfo.value = response.data
      } catch (error) {
        console.error('加载 SwanLab 信息失败:', error)
        swanlabInfo.value = {
          status: 'error',
          url: '',
          projects: []
        }
      }
    }

    // 启动 SwanLab
    const startSwanLab = async () => {
      startingSwanLab.value = true
      try {
        await trainingAPI.startSwanLab(swanlabConfig)
        ElMessage.success('SwanLab 启动成功')
        await loadSwanLabInfo()
      } catch (error) {
        ElMessage.error('启动 SwanLab 失败: ' + error.message)
      } finally {
        startingSwanLab.value = false
      }
    }

    // 打开 SwanLab
    const openSwanLab = () => {
      const url = swanlabInfo.value.url || `http://${swanlabConfig.host}:${swanlabConfig.port}`
      window.open(url, '_blank')
    }

    // 保存配置
    const saveConfig = async () => {
      savingConfig.value = true
      try {
        await trainingAPI.saveSwanLabConfig(swanlabConfig)
        ElMessage.success('配置保存成功')
      } catch (error) {
        ElMessage.error('保存配置失败: ' + error.message)
      } finally {
        savingConfig.value = false
      }
    }

    // 测试连接
    const testConnection = async () => {
      testingConnection.value = true
      try {
        await trainingAPI.testSwanLabConnection(swanlabConfig)
        ElMessage.success('连接测试成功')
      } catch (error) {
        ElMessage.error('连接测试失败: ' + error.message)
      } finally {
        testingConnection.value = false
      }
    }

    // 刷新项目列表
    const refreshProjects = async () => {
      loadingProjects.value = true
      try {
        await loadSwanLabInfo()
        ElMessage.success('项目列表刷新成功')
      } catch (error) {
        ElMessage.error('刷新项目列表失败')
      } finally {
        loadingProjects.value = false
      }
    }

    // 创建项目
    const createProject = () => {
      newProject.name = ''
      newProject.description = ''
      showCreateDialog.value = true
    }

    // 确认创建项目
    const confirmCreateProject = async () => {
      if (!newProject.name.trim()) {
        ElMessage.warning('请输入项目名称')
        return
      }
      
      creatingProject.value = true
      try {
        await trainingAPI.createSwanLabProject(newProject)
        ElMessage.success('项目创建成功')
        showCreateDialog.value = false
        await loadSwanLabInfo()
      } catch (error) {
        ElMessage.error('创建项目失败: ' + error.message)
      } finally {
        creatingProject.value = false
      }
    }

    // 打开项目
    const openProject = (project) => {
      const url = `${swanlabInfo.value.url}/project/${project.name}`
      window.open(url, '_blank')
    }

    // 删除项目
    const deleteProject = async (project) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除项目 "${project.name}" 吗？此操作不可恢复。`,
          '确认删除',
          {
            type: 'warning',
            confirmButtonText: '删除',
            cancelButtonText: '取消'
          }
        )
        
        await trainingAPI.deleteSwanLabProject(project.name)
        ElMessage.success('项目删除成功')
        await loadSwanLabInfo()
      } catch (error) {
        if (error !== 'cancel') {
          ElMessage.error('删除项目失败: ' + error.message)
        }
      }
    }

    onMounted(() => {
      loadSwanLabInfo()
    })

    return {
      swanlabInfo,
      swanlabConfig,
      loadingProjects,
      startingSwanLab,
      savingConfig,
      testingConnection,
      creatingProject,
      showCreateDialog,
      newProject,
      getStatusIcon,
      getStatusText,
      getProjectStatusType,
      formatTime,
      startSwanLab,
      openSwanLab,
      saveConfig,
      testConnection,
      refreshProjects,
      createProject,
      confirmCreateProject,
      openProject,
      deleteProject
    }
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}

.swanlab-status {
  margin-bottom: 20px;
}

.status-card {
  display: flex;
  align-items: center;
  padding: 16px;
  border: 1px solid #e4e7ed;
  border-radius: 8px;
  background: #fafafa;
}

.status-icon {
  margin-right: 12px;
  padding: 8px;
  border-radius: 50%;
  background: #f0f0f0;
}

.status-icon.running {
  background: #f0f9ff;
  color: #67c23a;
}

.status-icon.stopped {
  background: #fef0f0;
  color: #f56c6c;
}

.status-icon.starting {
  background: #f0f9ff;
  color: #409eff;
}

.status-icon.error {
  background: #fef0f0;
  color: #f56c6c;
}

.status-info h4 {
  margin: 0 0 4px 0;
  font-size: 14px;
  color: #606266;
}

.status-info p {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
  color: #303133;
}

.swanlab-config {
  margin-top: 20px;
}

.swanlab-config h4 {
  margin-bottom: 16px;
  color: #303133;
}

.projects-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
}

.project-card {
  transition: all 0.3s ease;
}

.project-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.project-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.project-name {
  font-weight: 500;
  color: #303133;
}

.project-content p {
  margin: 8px 0;
  font-size: 14px;
  color: #606266;
}

.project-content strong {
  color: #303133;
}

.project-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
}

.loading-container {
  padding: 20px;
}

.el-divider {
  margin: 24px 0;
}
</style> 