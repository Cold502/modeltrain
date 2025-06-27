<template>
  <div class="page-container">
    <h2>训练可视化 - SwanLab</h2>
    <p>查看模型训练过程和结果的可视化图表</p>
    
    <el-card style="margin-bottom: 20px;">
      <template #header>
        <div style="display: flex; justify-content: space-between; align-items: center;">
          <span>SwanLab 访问入口</span>
          <el-button type="primary" @click="openSwanLab">
            打开 SwanLab
          </el-button>
        </div>
      </template>
      
      <el-alert
        title="SwanLab 集成"
        type="success"
        :closable="false"
        show-icon
      >
        <p>SwanLab 是一个开源的机器学习实验跟踪平台，支持：</p>
        <ul style="margin: 8px 0; padding-left: 20px;">
          <li>实时监控训练指标</li>
          <li>可视化损失函数和准确率变化</li>
          <li>比较不同训练实验</li>
          <li>保存和分享训练结果</li>
        </ul>
      </el-alert>
    </el-card>

    <el-card>
      <template #header>
        <span>最近的训练项目</span>
      </template>
      
      <el-empty description="暂无训练项目" />
    </el-card>
  </div>
</template>

<script>
export default {
  name: 'SwanLabViz',
  methods: {
    openSwanLab() {
      // 打开 SwanLab 界面
      window.open('http://localhost:5092', '_blank')
    }
  }
}
</script>

<style scoped>
.page-container {
  padding: 20px;
}
</style> 