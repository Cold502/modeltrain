/**
 * 统一日志管理工具
 * 根据环境变量控制日志输出，避免生产环境泄露敏感信息
 */

const isDebug = import.meta.env.VITE_DEBUG_LOG === 'true'

/**
 * 调试日志 - 仅在开发环境输出
 */
export const log = (...args) => {
  if (isDebug) {
    console.log(...args)
  }
}

/**
 * 警告日志 - 始终输出
 */
export const warn = (...args) => {
  console.warn(...args)
}

/**
 * 错误日志 - 始终输出
 */
export const error = (...args) => {
  console.error(...args)
}

/**
 * 信息日志 - 始终输出
 */
export const info = (...args) => {
  console.info(...args)
}

/**
 * 安全日志 - 不输出敏感信息
 */
export const logSafe = (message, data = {}) => {
  if (isDebug) {
    // 过滤敏感字段
    const safeData = { ...data }
    const sensitiveKeys = ['token', 'password', 'authorization', 'cookie', 'secret', 'key']
    
    Object.keys(safeData).forEach(key => {
      if (sensitiveKeys.some(sensitive => key.toLowerCase().includes(sensitive))) {
        safeData[key] = '[FILTERED]'
      }
    })
    
    console.log(message, safeData)
  }
}
