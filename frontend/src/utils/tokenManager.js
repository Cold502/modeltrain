import axios from 'axios'
import store from '../store'
import router from '../router'

// 是否正在刷新token
let isRefreshing = false
// 等待刷新token的请求队列
let failedQueue = []
// 标记是否已经尝试过刷新token，避免无限循环
let hasAttemptedRefresh = false

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
    console.log('🔄 尝试刷新token...')
    
    // 确保发送cookie
    const response = await axios.post(
      `/api/auth/refresh`,  // 使用相对路径，通过代理转发
      {},  // 不需要传递refresh_token，会自动从cookie中读取
      { 
        withCredentials: true,  // 确保发送cookie
        headers: {
          'Content-Type': 'application/json'
        }
      }
    )
    
    const { access_token } = response.data
    localStorage.setItem('token', access_token)
    hasAttemptedRefresh = false // 重置标记
    console.log('✅ Token刷新成功')
    return access_token
  } catch (error) {
    console.error('❌ Token刷新失败:', error)
    hasAttemptedRefresh = true // 标记已尝试过刷新
    
    // 如果是401错误，说明refresh token无效，清除所有认证信息
    if (error.response && error.response.status === 401) {
      console.log('🔄 Refresh token无效，清除认证信息')
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      store.dispatch('logout')
      router.push('/login')
    }
    
    throw error
  }
}

// 统一的获取访问token方法
export async function getAccessToken() {
  try {
    // 获取当前token
    let token = localStorage.getItem('token')
    
    // 如果token不存在或无效，尝试刷新
    if (!token || token === 'null' || token === 'undefined') {
      // 如果已经尝试过刷新但失败了，直接抛出错误
      if (hasAttemptedRefresh) {
        console.log('⚠️ 已经尝试过刷新token，跳过')
        throw new Error('Token刷新失败，请重新登录')
      }
      
      if (isRefreshing) {
        // 如果正在刷新token，将请求加入队列
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
      }
      
      isRefreshing = true
      
      try {
        token = await refreshToken()
        processQueue(null, token)
        return token
      } catch (refreshError) {
        processQueue(refreshError, null)
        throw refreshError
      } finally {
        isRefreshing = false
      }
    }
    
    return token
  } catch (error) {
    console.error('获取访问token失败:', error)
    throw error
  }
}

// 处理401错误的统一方法
export async function handle401Error(originalRequest = null) {
  // 如果已经尝试过刷新但失败了，直接抛出错误
  if (hasAttemptedRefresh) {
    console.log('⚠️ 已经尝试过刷新token，跳过401处理')
    throw new Error('Token刷新失败，请重新登录')
  }
  
  if (isRefreshing) {
    // 如果正在刷新token，将请求加入队列
    return new Promise((resolve, reject) => {
      failedQueue.push({ resolve, reject })
    })
  }
  
  isRefreshing = true
  
  try {
    const newToken = await refreshToken()
    processQueue(null, newToken)
    return newToken
  } catch (refreshError) {
    processQueue(refreshError, null)
    throw refreshError
  } finally {
    isRefreshing = false
  }
}

// 统一的请求头生成方法
export async function getAuthHeaders(additionalHeaders = {}) {
  try {
    const token = await getAccessToken()
    return {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
      ...additionalHeaders
    }
  } catch (error) {
    console.error('获取认证头失败:', error)
    throw error
  }
}

// 创建带认证头的fetch请求 - 统一处理
export async function authenticatedFetch(url, options = {}) {
  try {
    const authHeaders = await getAuthHeaders(options.headers)
    
    const fetchOptions = {
      ...options,
      headers: authHeaders,
      credentials: 'include' // 确保发送cookie
    }
    
    const response = await fetch(url, fetchOptions)
    
    // 如果遇到401错误，尝试刷新token并重试
    if (response.status === 401) {
      try {
        const newToken = await handle401Error()
        
        // 使用新token重试请求
        const retryOptions = {
          ...fetchOptions,
          headers: {
            ...authHeaders,
            'Authorization': `Bearer ${newToken}`
          }
        }
        
        return await fetch(url, retryOptions)
      } catch (refreshError) {
        // 刷新失败，返回原始响应
        return response
      }
    }
    
    return response
  } catch (error) {
    console.error('认证fetch请求失败:', error)
    throw error
  }
}

// 创建SSE流式请求 - 专门处理SSE
export async function createSSEStream(url, requestData, onChunk, onComplete, onError) {
  try {
    console.log('🌐 准备发送SSE请求到:', url)
    console.log('📄 请求体:', requestData)

    const authHeaders = await getAuthHeaders({
      'Accept': 'text/event-stream',
      'Cache-Control': 'no-cache',
      'Connection': 'keep-alive'
    })
    
    const response = await fetch(url, {
      method: 'POST',
      headers: authHeaders,
      body: JSON.stringify(requestData),
      credentials: 'include'
    })

    console.log('📡 收到响应，状态码:', response.status)

    if (!response.ok) {
      // 如果是401错误，尝试刷新token并重试
      if (response.status === 401) {
        try {
          const newToken = await handle401Error()
          
          // 使用新token重试请求
          const retryHeaders = {
            ...authHeaders,
            'Authorization': `Bearer ${newToken}`
          }
          
          const retryResponse = await fetch(url, {
            method: 'POST',
            headers: retryHeaders,
            body: JSON.stringify(requestData),
            credentials: 'include'
          })
          
          if (!retryResponse.ok) {
            throw new Error(`HTTP ${retryResponse.status}: ${retryResponse.statusText}`)
          }
          
          return await processSSEResponse(retryResponse, onChunk, onComplete, onError)
        } catch (refreshError) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`)
        }
      } else {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }
    }

    return await processSSEResponse(response, onChunk, onComplete, onError)

  } catch (error) {
    console.error('💥 SSE流式处理错误:', error)
    if (onError) {
      onError(error)
    } else {
      throw error
    }
  }
}

// 处理SSE响应
async function processSSEResponse(response, onChunk, onComplete, onError) {
  // 检查响应是否支持流式读取
  if (!response.body) {
    throw new Error('响应数据为空')
  }

  console.log('✅ 开始读取SSE流式响应...')
  
  // 使用ReadableStream进行流式处理
  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let currentContent = ''
  let isDone = false
  let chunkCount = 0

  try {
    while (true) {
      const { done, value } = await reader.read()
      
      if (done) {
        console.log('✅ 数据流读取完成')
        break
      }

      chunkCount++
      console.log(`📦 读取到第${chunkCount}个数据块，长度:`, value.length)

      // 解码数据
      const chunkStr = decoder.decode(value, { stream: true })
      console.log(`📄 解码第${chunkCount}个数据块:`, chunkStr)
      buffer += chunkStr
      console.log('쌓 增加缓冲区，当前缓冲区长度:', buffer.length)

      // 处理完整的行
      while (buffer.includes('\n')) {
        const lineEndIndex = buffer.indexOf('\n')
        const line = buffer.slice(0, lineEndIndex).trim()
        buffer = buffer.slice(lineEndIndex + 1)
        console.log('✂️ 处理一行数据:', line)
        console.log('💾 剩余缓冲区长度:', buffer.length)

        if (!line) {
          console.log('⚠️ 空行，跳过处理')
          continue
        }

        // 处理SSE格式的数据
        if (line.startsWith('data: ')) {
          const data = line.slice(6) // 移除 'data: ' 前缀
          console.log('📨 处理data行，内容:', data)

          // 检查特殊标记
          if (data === '[DONE]') {
            console.log('🏁 收到[DONE]标记，结束流式传输')
            isDone = true
            break
          }

          if (data.startsWith('[ERROR]')) {
            const errorMsg = data.slice(7) // 移除 '[ERROR]' 前缀
            console.error('💥 收到错误信息:', errorMsg)
            throw new Error(errorMsg)
          }

          // 添加内容到当前消息
          if (data) {
            currentContent += data
            console.log('➕ 累积内容，当前总长度:', currentContent.length)

            // 调用回调函数更新内容
            if (onChunk) {
              onChunk(currentContent)
            }
          }
        } else {
          console.log('⏭️ 非data行，跳过处理:', line)
        }
        // 忽略其他类型的SSE行 (如 event:, id:, retry: 等)
      }

      if (isDone) {
        break
      }
    }
  } finally {
    reader.releaseLock()
  }

  // 调用完成回调
  if (onComplete) {
    onComplete(currentContent)
  }
}

// 调试方法：检查refresh token状态
export function debugRefreshToken() {
  console.log('🔍 检查Refresh Token状态:')
  
  // 检查localStorage中的token
  const accessToken = localStorage.getItem('token')
  console.log('📱 localStorage中的access_token:', accessToken ? `${accessToken.substring(0, 20)}...` : '不存在')
  
  // 检查cookie中的refresh_token（只能检查是否存在，不能读取内容）
  const cookies = document.cookie.split(';')
  const refreshTokenCookie = cookies.find(cookie => cookie.trim().startsWith('refresh_token='))
  console.log('🍪 Cookie中的refresh_token:', refreshTokenCookie ? '存在' : '不存在')
  
  if (refreshTokenCookie) {
    console.log('🍪 Refresh token cookie详情:', refreshTokenCookie.trim())
  }
  
  // 检查当前认证状态
  console.log('🔐 当前认证状态:', {
    hasAccessToken: !!accessToken,
    hasRefreshTokenCookie: !!refreshTokenCookie,
    isLoggedIn: store.state.isLoggedIn
  })
  
  return {
    hasAccessToken: !!accessToken,
    hasRefreshTokenCookie: !!refreshTokenCookie,
    isLoggedIn: store.state.isLoggedIn
  }
}

// 导出统一的token管理方法
export default {
  getAccessToken,
  handle401Error,
  getAuthHeaders,
  authenticatedFetch,
  createSSEStream,
  debugRefreshToken
}
