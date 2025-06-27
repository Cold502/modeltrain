<template>
  <div class="page-container">
    <h2>模型训练</h2>
    <p>基于LlamaFactory的模型微调训练平台</p>
    <el-alert
      title="功能说明"
      type="info"
      :closable="false"
      show-icon
    >
      <ul style="margin: 8px 0; padding-left: 20px;">
        <li>集成LlamaFactory训练脚本</li>
        <li>支持上传和管理训练数据集</li>
        <li>可保存和复用训练配置</li>
        <li>支持VLLM模型加载和卸载</li>
        <li>实时查看训练日志和进度</li>
      </ul>
    </el-alert>
  </div>
</template>

<script>
export default {
  name: 'ModelTraining'
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
</style> 