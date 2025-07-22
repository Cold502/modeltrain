<template>
  <div class="dashboard-content">
    <div class="welcome-section">
      <h2>欢迎使用企业模型训练平台</h2>
      <p>一站式模型训练、测试与管理解决方案</p>
    </div>
    
    <!-- 功能卡片 -->
    <div class="feature-cards">
      <el-card class="feature-card" @click="$router.push('/dashboard/chat')">
        <div class="card-icon">
          <el-icon size="56" color="#64a8db"><ChatDotRound /></el-icon>
        </div>
        <h3>模型对话</h3>
        <p>与AI模型进行智能对话，支持多模型切换</p>
      </el-card>
      
      <el-card class="feature-card" @click="$router.push('/dashboard/model-test')">
        <div class="card-icon">
          <el-icon size="56" color="#7bb3f0"><Monitor /></el-icon>
        </div>
        <h3>模型测试</h3>
        <p>对比测试多个模型，评估模型性能</p>
      </el-card>
      
      <el-card class="feature-card" @click="$router.push('/dashboard/training')">
        <div class="card-icon">
          <el-icon size="56" color="#8bc5f5"><Monitor /></el-icon>
        </div>
        <h3>模型训练</h3>
        <p>基于LlamaFactory的模型微调训练</p>
      </el-card>
      
      <el-card class="feature-card" @click="$router.push('/dashboard/training-viz')">
        <div class="card-icon">
          <el-icon size="56" color="#9ed7fa"><TrendCharts /></el-icon>
        </div>
        <h3>训练可视化</h3>
        <p>通过SwanLab查看训练过程和结果</p>
      </el-card>
    </div>
    
    <!-- 快速统计 -->
    <div class="stats-section">
      <el-row :gutter="24">
        <el-col :span="6">
          <el-card class="stat-card">
            <el-statistic title="可用模型" :value="modelStats.available" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <el-statistic title="训练任务" :value="trainingStats.total" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <el-statistic title="对话会话" :value="chatStats.sessions" />
          </el-card>
        </el-col>
        <el-col :span="6">
          <el-card class="stat-card">
            <el-statistic title="数据集" :value="datasetStats.total" />
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useStore } from 'vuex'
import { useRouter } from 'vue-router'
import {
  ChatDotRound,
  Monitor,
  TrendCharts
} from '@element-plus/icons-vue'
import { modelAPI, trainingAPI, chatAPI } from '../utils/api'

export default {
  name: 'Dashboard',
  components: {
    ChatDotRound,
    Monitor,
    TrendCharts
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    
    const modelStats = ref({ available: 0, total: 0 })
    const trainingStats = ref({ total: 0, running: 0 })
    const chatStats = ref({ sessions: 0 })
    const datasetStats = ref({ total: 0 })
    
    const loadStats = async () => {
      try {
        // 加载模型统计
        const response = await modelAPI.getModels()
        const models = Array.isArray(response.data) ? response.data : []
        modelStats.value = {
          available: models.filter(m => m.status === 'active').length,
          total: models.length
        }
        
        // 加载训练任务统计
        const tasksResponse = await trainingAPI.getTrainingTasks()
        const tasks = Array.isArray(tasksResponse.data) ? tasksResponse.data : []
        trainingStats.value = {
          total: tasks.length,
          running: tasks.filter(t => t.status === 'running').length
        }
        
        // 加载对话会话统计
        const sessionsResponse = await chatAPI.getSessions()
        const sessions = Array.isArray(sessionsResponse.data) ? sessionsResponse.data : []
        chatStats.value = {
          sessions: sessions.length
        }
        
        // 加载数据集统计
        const datasetsResponse = await trainingAPI.getDatasets()
        const datasets = Array.isArray(datasetsResponse.data) ? datasetsResponse.data : []
        datasetStats.value = {
          total: datasets.length
        }
        
      } catch (error) {
        console.error('加载统计数据失败:', error)
      }
    }
    
    onMounted(() => {
      // 加载统计数据
      loadStats()
    })
    
    return {
      modelStats,
      trainingStats,
      chatStats,
      datasetStats
    }
  }
}
</script>

<style scoped>
.dashboard-content {
  width: 100%;
  max-width: none;
}

.welcome-section {
  margin-bottom: 2.5rem;
  text-align: center;
  padding: 2rem;
  background: var(--card-bg);
  border-radius: 16px;
  box-shadow: 0 6px 24px rgba(100, 168, 219, 0.15);
  border: 2px solid var(--border-color);
}

.welcome-section h2 {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--dark-blue);
  margin: 0 0 0.8rem 0;
  letter-spacing: 1px;
}

.welcome-section p {
  color: var(--primary-blue);
  font-size: 1.4rem;
  margin: 0;
  font-weight: 500;
}

.feature-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 1.8rem;
  margin-bottom: 2.5rem;
}

.feature-card {
  cursor: pointer;
  text-align: center;
  padding: 2.2rem 1.8rem;
  border-radius: 16px;
  background: var(--card-bg);
  border: 2px solid var(--border-color);
  box-shadow: 0 6px 20px rgba(100, 168, 219, 0.1);
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 36px rgba(100, 168, 219, 0.25);
  border-color: var(--medium-blue);
}

.card-icon {
  margin-bottom: 1.2rem;
}

.feature-card h3 {
  font-size: 1.4rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0.8rem 0;
}

.feature-card p {
  color: var(--primary-blue);
  font-size: 1rem;
  margin: 0;
  line-height: 1.5;
  font-weight: 400;
}

.stats-section {
  margin-top: 2.5rem;
}

.stat-card {
  text-align: center;
  padding: 1.8rem;
  border-radius: 12px;
  background: var(--card-bg);
  border: 2px solid var(--border-color);
  box-shadow: 0 4px 16px rgba(100, 168, 219, 0.1);
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(100, 168, 219, 0.2);
  border-color: var(--medium-blue);
}

.stat-card :deep(.el-statistic__head) {
  font-size: 1.1rem !important;
  color: var(--primary-blue) !important;
  font-weight: 600 !important;
  margin-bottom: 0.8rem !important;
}

.stat-card :deep(.el-statistic__content) {
  font-size: 2.2rem !important;
  color: var(--dark-blue) !important;
  font-weight: 700 !important;
}
</style> 