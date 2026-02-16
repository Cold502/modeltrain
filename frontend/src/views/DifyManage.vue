<template>
  <div class="dify-manage-container">
    <div class="dify-header">
      <h2>Dify 应用管理</h2>
      <div class="header-actions">
        <el-tag :type="healthStatus.status === 'running' ? 'success' : 'danger'">
          {{ healthStatus.message }}
        </el-tag>
        <el-button @click="openDifyConsole" type="primary" :icon="Link">
          打开Dify控制台
        </el-button>
      </div>
    </div>
    
    <div class="dify-content">
      <iframe 
        v-if="healthStatus.status === 'running'"
        :src="difyWebUrl" 
        frameborder="0"
        class="dify-iframe"
        @load="onIframeLoad"
      />
      <div v-else class="dify-placeholder">
        <el-empty description="Dify 服务未运行">
          <template #default>
            <p style="color: var(--el-text-color-secondary); margin-bottom: 12px;">请先通过 dev.bat 或 docker compose 启动 Dify 服务</p>
            <el-button type="primary" @click="checkHealth">重新检测</el-button>
          </template>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { difyAPI } from '@/utils/api'

const difyWebUrl = `http://${window.location.hostname}`
const healthStatus = ref({
  status: 'unknown',
  message: '检查中...'
})

const checkHealth = async () => {
  try {
    const response = await difyAPI.checkHealth()
    healthStatus.value = {
      status: response.data.status,
      message: response.data.message || response.data.status
    }
  } catch (error) {
    healthStatus.value = {
      status: 'error',
      message: '无法连接到Dify服务'
    }
  }
}

const openDifyConsole = () => {
  window.open(difyWebUrl, '_blank')
}

const onIframeLoad = () => {
  console.log('Dify界面加载完成')
}

onMounted(() => {
  checkHealth()
})
</script>

<style scoped>
.dify-manage-container {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--el-bg-color-page);
}

.dify-header {
  padding: 20px 24px;
  background: var(--el-bg-color);
  border-bottom: 1px solid var(--el-border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.dify-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--el-text-color-primary);
}

.header-actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.dify-content {
  flex: 1;
  overflow: hidden;
  padding: 16px;
}

.dify-iframe {
  width: 100%;
  height: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  background: var(--el-bg-color);
}

.dify-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  background: var(--el-bg-color);
  border-radius: 8px;
}
</style>
