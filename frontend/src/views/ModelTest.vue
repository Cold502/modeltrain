<template>
  <div class="page-container">
    <h2>模型测试</h2>
    <p>此页面正在开发中，将提供模型对比测试功能。</p>
    <el-alert
      title="功能说明"
      type="info"
      :closable="false"
      show-icon
    >
      <ul style="margin: 8px 0; padding-left: 20px;">
        <li>支持上传图片进行测试</li>
        <li>最多可同时选择3个模型进行对比</li>
        <li>支持流式输出和普通输出模式</li>
        <li>提供测试历史记录</li>
      </ul>
    </el-alert>
  </div>
</template>

<script>
export default {
  name: 'ModelTest'
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
</style> 