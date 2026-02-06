import axios from 'axios'
import { message } from './message'
import store from '../store'
import router from '../router'
import { getAccessToken, handle401Error, getAuthHeaders } from './tokenManager'
import { log, logSafe, error as logError } from './logger'

// 读取环境变量中的 API 基地址，默认为 '/api'。
// 开发模式下使用绝对后端URL
const inferDevApiBase = () => {
  if (typeof window === 'undefined') return '/api'
  if (import.meta.env.DEV) {
    return 'http://127.0.0.1:8000/api'
  }
  return '/api'
}

const apiBaseURL = (import.meta.env?.VITE_API_BASE_URL?.trim()) || inferDevApiBase()

console.log('🔍 API配置:')
console.log('  DEV模式:', import.meta.env.DEV)
console.log('  配置的baseURL:', apiBaseURL)

// 创建axios实例
const api = axios.create({
  baseURL: apiBaseURL,
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json'
  }
})

console.log('🔍 axios实例配置:')
console.log('  实例baseURL:', api.defaults.baseURL)
console.log('  实例headers:', api.defaults.headers)

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
        logError('获取token失败:', error)
        // 如果是token刷新失败，不要继续请求
        if (error.message === 'Token刷新失败，请重新登录') {
          throw error
        }
      }
    }
    
    logSafe('🌐 发送请求:', {
      method: config.method?.toUpperCase(),
      url: config.url,
      withCredentials: config.withCredentials
    })
    
    return config
  },
  error => {
    logError('请求错误:', error)
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    logSafe('✅ 收到响应:', {
      status: response.status,
      url: response.config.url
    })
    return response
  },
  async axiosError => {
    logError('响应错误:', axiosError)
    
    const originalRequest = axiosError.config
    
    // 如果是401错误且不是刷新token的请求，且不是登录/注册请求
    if (axiosError.response?.status === 401 && 
        !originalRequest._retry && 
        !originalRequest.url?.includes('/auth/login') && 
        !originalRequest.url?.includes('/auth/register')) {
      try {
        // 使用统一的401错误处理方法
        const newToken = await handle401Error(originalRequest)
        originalRequest.headers.Authorization = `Bearer ${newToken}`
        originalRequest._retry = true // 标记已重试
        return api(originalRequest)
      } catch (refreshError) {
        // 如果刷新失败，直接返回错误，不要继续尝试
        logError('Token刷新失败，停止重试:', refreshError)
        return Promise.reject(refreshError)
      }
    }
    
    // 只处理真正需要全局处理的错误
    if (axiosError.response) {
      const { status } = axiosError.response
      
      if (status === 401) {
        // 401是唯一需要全局处理的错误（token失效）
        // 但是登录/注册的401错误应该由页面处理，不是全局处理
        const isAuthRequest = originalRequest.url?.includes('/auth/login') || 
                             originalRequest.url?.includes('/auth/register')
        
        if (!isAuthRequest && router.currentRoute.value.name !== 'Login') {
          log('Token无效，清除本地存储')
          store.dispatch('logout');
          message.error('认证已过期，请重新登录');
          router.push('/login');
        }
      } else if (status === 404) {
        // 404错误通常由页面处理，但登录的404（账户不存在）应该由登录页面处理
        const isAuthRequest = originalRequest.url?.includes('/auth/login') || 
                             originalRequest.url?.includes('/auth/register')
        
        if (!isAuthRequest) {
          // 非认证请求的404错误可以全局处理
          message.error('请求的资源不存在')
        }
      }
      // 其他所有错误都由具体页面处理
    } else if (axiosError.request) {
      // 网络错误可以全局处理
      message.error('网络错误，请检查网络连接')
    } else {
      // 请求配置错误
      message.error('请求配置错误')
    }
    
    return Promise.reject(axiosError)
  }
)


// API方法定义
export const authAPI = {
  // 用户注册
  register: (userData) => api.post('/auth/register', userData),
  
  // 用户登录
  login: (loginData) => {
    logSafe('🔐 发送登录请求:', { username: loginData.username })
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
    log('🔄 发送token刷新请求')
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

export const difyAPI = {
  // 健康检查
  checkHealth: () => api.get('/dify/health'),
  
  // 获取知识库列表
  getDatasets: (params = {}) => api.get('/dify/datasets', { params }),
  
  // 获取工作流列表
  getWorkflows: () => api.get('/dify/workflows'),
  
  // RAG对话
  chat: (chatData) => api.post('/dify/chat', chatData),
  
  // 工作流执行
  runWorkflow: (appId, inputs) => api.post(`/dify/workflows/${appId}/run`, { inputs })
}

export default api