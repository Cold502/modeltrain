import { ElMessage } from 'element-plus';

/**
 * 封装 ElMessage，提供默认可关闭功能
 *
 * @param {object} options - ElMessage 的配置选项
 * @returns {object} ElMessage 实例
 */
const showClosableMessage = (options) => {
  return ElMessage({
    showClose: true,
    duration: 3000,
    ...options,
  });
};

/**
 * 封装后的消息提示对象
 */
export const message = {
  /**
   * 显示成功消息
   * @param {string} msg - 消息内容
   * @param {object} options - 其他 ElMessage 选项
   */
  success: (msg, options = {}) => {
    return showClosableMessage({
      message: msg,
      type: 'success',
      ...options,
    });
  },
  /**
   * 显示错误消息
   * @param {string} msg - 消息内容
   * @param {object} options - 其他 ElMessage 选项
   */
  error: (msg, options = {}) => {
    return showClosableMessage({
      message: msg,
      type: 'error',
      ...options,
    });
  },
  /**
   * 显示警告消息
   * @param {string} msg - 消息内容
   * @param {object} options - 其他 ElMessage 选项
   */
  warning: (msg, options = {}) => {
    return showClosableMessage({
      message: msg,
      type: 'warning',
      ...options,
    });
  },
  /**
   * 显示普通消息
   * @param {string} msg - 消息内容
   * @param {object} options - 其他 ElMessage 选项
   */
  info: (msg, options = {}) => {
    return showClosableMessage({
      message: msg,
      type: 'info',
      ...options,
    });
  },
}; 