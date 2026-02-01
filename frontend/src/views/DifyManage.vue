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
        :src="difyWebUrl" 
        frameborder="0"
        class="dify-iframe"
        @load="onIframeLoad"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { Link } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import api from '@/utils/api'

const difyWebUrl = import.meta.env.VITE_DIFY_WEB_URL || 'http://localhost:3000'
const healthStatus = ref({
  status: 'unknown',
  message: '检查中...'
})

const checkHealth = async () => {
  try {
    const response = await api.dify.checkHealth()
    healthStatus.value = {
      status: response.status,
      message: response.message || response.status
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
  background: #f5f7fa;
}

.dify-header {
  padding: 20px 24px;
  background: white;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.dify-header h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #303133;
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
  background: white;
}
</style>
