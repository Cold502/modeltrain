import axios from 'axios'
import { ElMessage } from 'element-plus'
import { message } from './message'
import store from '../store'
import router from '../router'
import { getAccessToken, handle401Error, getAuthHeaders } from './tokenManager'

// 创建axios实例
const api = axios.create({
  baseURL: '/api',  // 使用相对路径，通过代理转发
  timeout: 30000,
  withCredentials: true,  // 确保发送cookie
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  async config => {
    // 确保每个请求都发送cookie
    config.withCredentials = true
    
    // 对于登录和注册请求，不需要添加Authorization头
    const isAuthRequest = config.url?.includes('/auth/login') || 
                         config.url?.includes('/auth/register') ||
                         config.url?.includes('/auth/refresh')
    
    if (!isAuthRequest) {
      try {
        // 使用统一的token获取方法
        const token = await getAccessToken()
        config.headers.Authorization = `Bearer ${token}`
      } catch (error) {
        console.error('获取token失败:', error)
        // 如果是token刷新失败，不要继续请求
        if (error.message === 'Token刷新失败，请重新登录') {
          throw error
        }
      }
    }
    
    console.log('🌐 发送请求:', config.method?.toUpperCase(), config.url)
    console.log('📋 请求头:', config.headers)
    console.log('🍪 withCredentials:', config.withCredentials)
    
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
    console.log('✅ 收到响应:', response.status, response.config.url)
    return response
  },
  async error => {
    console.error('响应错误:', error)
    
    const originalRequest = error.config
    
    // 如果是401错误且不是刷新token的请求
    if (error.response?.status === 401 && !originalRequest._retry) {
      try {
        // 使用统一的401错误处理方法
        const newToken = await handle401Error(originalRequest)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        originalRequest._retry = true // 标记已重试
        return api(originalRequest)
      } catch (refreshError) {
        // 如果刷新失败，直接返回错误，不要继续尝试
        console.error('Token刷新失败，停止重试:', refreshError)
        return Promise.reject(refreshError)
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

// 创建带认证的axios请求方法
export async function authenticatedRequest(config) {
  try {
    // 使用统一的认证头生成方法
    const authHeaders = await getAuthHeaders(config.headers)
    
    const requestConfig = {
      ...config,
      headers: authHeaders,
      withCredentials: true
    }
    
    const response = await axios(requestConfig)
    
    // 如果遇到401错误，尝试刷新token并重试
    if (response.status === 401) {
      try {
        const newToken = await handle401Error()
        
        // 使用新token重试请求
        const retryConfig = {
          ...requestConfig,
          headers: {
            ...authHeaders,
            'Authorization': `Bearer ${newToken}`
          }
        }
        
        return await axios(retryConfig)
      } catch (refreshError) {
        // 刷新失败，返回原始响应
        return response
      }
    }
    
    return response
  } catch (error) {
    console.error('认证axios请求失败:', error)
    throw error
  }
}

// API方法定义
export const authAPI = {
  // 用户注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 用户登录
  login: (loginData) => {
    console.log('🔐 发送登录请求:', loginData)
    return api.post('/auth/login', loginData)
  },
  
  // 用户登出
  logout: () => api.post('/auth/logout'),
  
  // 重置密码
  resetPassword: (resetData) => api.post('/auth/reset-password', resetData),
  
  // 获取当前用户信息
  getCurrentUser: () => api.get('/auth/me'),
  
  // 刷新token
  refreshToken: () => {
    console.log('🔄 发送token刷新请求')
    return api.post('/auth/refresh')
  }
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