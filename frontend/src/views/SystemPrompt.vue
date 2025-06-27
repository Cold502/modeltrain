<template>
  <div class="page-container">
    <h2>系统提示词管理</h2>
    <p>创建和管理模型的系统提示词</p>
    <el-alert
      title="功能说明"
      type="info"
      :closable="false"
      show-icon
    >
      <ul style="margin: 8px 0; padding-left: 20px;">
        <li>创建和编辑自定义系统提示词</li>
        <li>设置默认系统提示词</li>
        <li>在对话中快速切换提示词</li>
        <li>提示词模板管理</li>
      </ul>
    </el-alert>
  </div>
</template>

<script>
export default {
  name: 'SystemPrompt'
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
</style> 