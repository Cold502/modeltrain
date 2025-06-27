import axios from 'axios'
import { message } from './message'
import store from '../store'
import router from '../router'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  config => {
    const user = store.state.user
    if (user && user.id) {
      // 添加用户ID到请求参数中（简化版认证）
      if (config.method === 'get' || config.method === 'delete') {
        config.params = { ...config.params, user_id: user.id }
      } else {
        config.data = { ...config.data, user_id: user.id }
      }
    }
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response.data
  },
  error => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 如果是登录页的401，说明是密码或账号错误
          if (router.currentRoute.value.name === 'Login') {
            message.error(data.detail || '登录认证失败');
          } else {
            // 如果是其他页面的401，说明是token失效，需要重新登录
            message.error('认证已过期，请重新登录');
            store.dispatch('logout');
            router.push('/login');
          }
          break
        case 403:
          message.error(data.detail || '权限不足');
          break
        case 404:
          message.error(data.detail || '请求的资源不存在')
          break
        case 500:
          message.error('服务器内部错误')
          break
        default:
          message.error(data.detail || '请求失败')
      }
    } else {
      message.error('网络错误，请检查网络连接')
    }
    
    return Promise.reject(error)
  }
)

// API方法定义
export const authAPI = {
  // 用户注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 用户登录
  login: (loginData) => api.post('/auth/login', loginData),
  
  // 重置密码
  resetPassword: (resetData) => api.post('/auth/reset-password', resetData),
  
  // 获取当前用户信息
  getCurrentUser: (userId) => api.get('/auth/me', { params: { user_id: userId } })
}

export const chatAPI = {
  // 获取聊天会话列表
  getSessions: () => api.get('/chat/sessions'),
  
  // 创建新会话
  createSession: (sessionData) => api.post('/chat/sessions', sessionData),
  
  // 获取会话详情
  getSession: (sessionId) => api.get(`/chat/sessions/${sessionId}`),
  
  // 更新会话
  updateSession: (sessionId, sessionData) => api.put(`/chat/sessions/${sessionId}`, sessionData),
  
  // 删除会话
  deleteSession: (sessionId) => api.delete(`/chat/sessions/${sessionId}`),
  
  // 发送消息
  sendMessage: (messageData) => api.post('/chat/messages', messageData),
  
  // 导出会话
  exportSession: (sessionId) => api.get(`/chat/sessions/${sessionId}/export`, { responseType: 'blob' }),
  
  // 系统提示词管理
  getSystemPrompts: () => api.get('/chat/system-prompts'),
  createSystemPrompt: (promptData) => api.post('/chat/system-prompts', promptData),
  updateSystemPrompt: (promptId, promptData) => api.put(`/chat/system-prompts/${promptId}`, promptData),
  deleteSystemPrompt: (promptId) => api.delete(`/chat/system-prompts/${promptId}`)
}

export const modelAPI = {
  // 获取模型列表
  getModels: () => api.get('/model/list'),
  
  // 加载模型
  loadModel: (modelId) => api.post(`/model/load/${modelId}`),
  
  // 卸载模型
  unloadModel: (modelId) => api.post(`/model/unload/${modelId}`),
  
  // 模型测试
  testModels: (testData) => api.post('/model/test', testData),
  
  // 获取测试历史
  getTestHistory: () => api.get('/model/test/history'),
  
  // 上传图片
  uploadImage: (file) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/model/upload-image', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  
  // 添加模型
  addModel: (modelData) => api.post('/model/add', modelData)
}

export const modelConfigAPI = {
  getModels: () => api.get('/config/models'),
  addModel: (modelData) => api.post('/config/models', modelData),
  updateModel: (modelId, modelData) => api.put(`/config/models/${modelId}`, modelData),
  deleteModel: (modelId) => api.delete(`/config/models/${modelId}`),
}

export const trainingAPI = {
  // 数据集管理
  uploadDataset: (file, name, description) => {
    const formData = new FormData()
    formData.append('file', file)
    if (name) formData.append('name', name)
    if (description) formData.append('description', description)
    return api.post('/training/datasets', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },
  getDatasets: () => api.get('/training/datasets'),
  deleteDataset: (datasetId) => api.delete(`/training/datasets/${datasetId}`),
  
  // 训练任务管理
  createTrainingTask: (taskData) => api.post('/training/tasks', taskData),
  getTrainingTasks: () => api.get('/training/tasks'),
  startTraining: (taskId) => api.post(`/training/tasks/${taskId}/start`),
  stopTraining: (taskId) => api.post(`/training/tasks/${taskId}/stop`),
  getTrainingLogs: (taskId) => api.get(`/training/tasks/${taskId}/logs`),
  
  // SwanLab
  getSwanLabInfo: () => api.get('/training/swanlab')
}

export const adminAPI = {
  // 用户管理
  getAllUsers: () => api.get('/admin/users'),
  deleteUser: (userId) => api.delete(`/admin/users/${userId}`),
  updateUserRole: (userId, isAdmin) => api.put(`/admin/users/${userId}/role`, { is_admin: isAdmin }),
  
  // 系统统计
  getAdminStats: () => api.get('/admin/stats')
}

export default api 