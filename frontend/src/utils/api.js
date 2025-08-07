import axios from 'axios'
import { ElMessage } from 'element-plus'
import { message } from './message'
import store from '../store'
import router from '../router'

// 创建axios实例
const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 是否正在刷新token
let isRefreshing = false
// 等待刷新token的请求队列
let failedQueue = []

// 处理队列中的请求
const processQueue = (error, token = null) => {
  failedQueue.forEach(prom => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  
  failedQueue = []
}

// 刷新token的函数
const refreshToken = async () => {
  try {
    const refresh_token = localStorage.getItem('refresh_token')
    if (!refresh_token) {
      throw new Error('No refresh token')
    }
    
    const response = await axios.post(
      `${import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api'}/auth/refresh`,
      { refresh_token }
    )
    
    const { access_token } = response.data
    localStorage.setItem('token', access_token)
    return access_token
  } catch (error) {
    console.error('Token刷新失败:', error)
    // 清除所有token
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    store.dispatch('logout')
    router.push('/login')
    throw error
  }
}

// 请求拦截器
api.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    // 只在token存在且不为空时才添加Authorization头
    if (token && token.trim() !== '' && token !== 'null' && token !== 'undefined') {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => {
    console.error('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response
  },
  async error => {
    console.error('响应错误:', error)
    
    const originalRequest = error.config
    
    // 如果是401错误且不是刷新token的请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      if (isRefreshing) {
        // 如果正在刷新token，将请求加入队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        }).then(token => {
          originalRequest.headers.Authorization = `Bearer ${token}`
          return api(originalRequest)
        }).catch(err => {
          return Promise.reject(err)
        })
      }
      
      originalRequest._retry = true
      isRefreshing = true
      
      try {
        const newToken = await refreshToken()
        processQueue(null, newToken)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        return api(originalRequest)
      } catch (refreshError) {
        processQueue(refreshError, null)
        return Promise.reject(refreshError)
      } finally {
        isRefreshing = false
      }
    }
    
    // 处理其他错误
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // 如果是登录页的401，说明是密码或账号错误
          if (router.currentRoute.value.name === 'Login') {
            message.error(data.detail || '登录认证失败');
          } else {
            // 如果是其他页面的401，说明是token失效，清除本地存储
            console.log('Token无效，清除本地存储')
            store.dispatch('logout');
            // 只有在非登录页面才跳转
            if (router.currentRoute.value.name !== 'Login') {
              message.error('认证已过期，请重新登录');
              router.push('/login');
            }
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
          message.error(data.detail || `请求失败 (${status})`)
      }
    } else if (error.request) {
      message.error('网络错误，请检查网络连接')
    } else {
      message.error('请求配置错误')
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
  getCurrentUser: () => api.get('/auth/me'),
  
  // 刷新token
  refreshToken: (refreshToken) => api.post('/auth/refresh', { refresh_token: refreshToken })
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
  getProviders: () => api.get('/model-config/providers'),
  getModels: () => api.get('/model-config/'),
  addModel: (modelData) => api.post('/model-config/', modelData),
  updateModel: (modelId, modelData) => api.put(`/model-config/${modelId}`, modelData),
  deleteModel: (modelId) => api.delete(`/model-config/${modelId}`),
  getAvailableModels: (providerId) => api.get('/model-config/models', { params: { provider_id: providerId } }),
  refreshModels: (refreshData) => api.post('/model-config/models/refresh', refreshData),
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
  
  // SwanLab 管理
  getSwanLabInfo: () => api.get('/training/swanlab'),
  startSwanLab: (config) => api.post('/training/swanlab/start', config),
  stopSwanLab: () => api.post('/training/swanlab/stop'),
  saveSwanLabConfig: (config) => api.post('/training/swanlab/config', config),
  testSwanLabConnection: (config) => api.post('/training/swanlab/test', config),
  createSwanLabProject: (project) => api.post('/training/swanlab/projects', project),
  deleteSwanLabProject: (projectName) => api.delete(`/training/swanlab/projects/${projectName}`),
  getSwanLabProjects: () => api.get('/training/swanlab/projects')
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