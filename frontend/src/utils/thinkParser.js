/**
 * 思维过程解析工具
 * 用于统一处理流式和非流式响应中的 <think>...</think> 标签
 */

/**
 * 解析内容中的思维过程标签
 * @param {string} content - 原始内容
 * @returns {Object} 解析结果
 * @returns {string} result.content - 去除思维过程标签后的内容
 * @returns {string} result.thinking - 思维过程内容（如果有）
 * @returns {boolean} result.hasThinking - 是否包含思维过程
 */
export function parseThinkingContent(content) {
  if (!content || typeof content !== 'string') {
    return {
      content: content || '',
      thinking: '',
      hasThinking: false
    }
  }

  // 检查是否包含完整的思维过程标签
  if (content.includes('<think>') && content.includes('</think>')) {
    const thinkMatch = content.match(/<think>(.*?)<\/think>/s)
    if (thinkMatch) {
      return {
        content: content.replace(/<think>.*?<\/think>/s, '').trim(),
        thinking: thinkMatch[1].trim(),
        hasThinking: true
      }
    }
  }
  
  // 处理流式过程中的不完整标签（只有开始标签）
  if (content.includes('<think>') && !content.includes('</think>')) {
    const thinkStartIndex = content.indexOf('<think>')
    const thinkingContent = content.substring(thinkStartIndex + 7) // 7 = '<think>'.length
    const beforeThink = content.substring(0, thinkStartIndex)
    
    return {
      content: beforeThink.trim(),
      thinking: thinkingContent.trim(),
      hasThinking: true
    }
  }

  return {
    content: content.trim(),
    thinking: '',
    hasThinking: false
  }
}

/**
 * 为消息对象添加思维过程相关属性
 * @param {Object} message - 消息对象
 * @param {string} content - 原始内容
 * @returns {Object} 更新后的消息对象
 */
export function enrichMessageWithThinking(message, content) {
  const parsed = parseThinkingContent(content)
  
  return {
    ...message,
    content: parsed.content,
    thinking: parsed.thinking,
    showThinking: parsed.hasThinking
  }
}
