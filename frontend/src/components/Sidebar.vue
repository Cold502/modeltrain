<template>
  <div class="sidebar">
    <div class="logo">
      <h3>企业模型训练平台</h3>
    </div>
    
    <el-menu
      :default-active="activeIndex"
      class="el-menu-vertical"
      router
      @select="handleSelect"
    >
      <el-menu-item
        v-for="item in menuItems"
        :key="item.path"
        :index="item.path"
      >
        <el-icon>
          <component :is="item.icon" />
        </el-icon>
        <span>{{ item.label }}</span>
      </el-menu-item>
    </el-menu>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useRoute } from 'vue-router'
import {
  House,
  Setting,
  DataAnalysis,
  ChatDotRound,
  TrendCharts,
  Document
} from '@element-plus/icons-vue'

const route = useRoute()

const menuItems = [
  {
    path: '/dashboard',
    icon: 'House',
    label: '首页'
  },
  {
    path: '/model-config',
    icon: 'Setting',
    label: '模型配置'
  },
  {
    path: '/model-test',
    icon: 'DataAnalysis',
    label: '模型测试'
  },
  {
    path: '/chat',
    icon: 'ChatDotRound',
    label: '模型对话'
  },
  {
    path: '/training',
    icon: 'TrendCharts',
    label: '模型训练'
  },
  {
    path: '/prompt-management',
    icon: 'Document',
    label: '提示词管理'
  }
]

const activeIndex = computed(() => route.path)

const handleSelect = (key, keyPath) => {
  console.log('Selected menu:', key, keyPath)
}
</script>

<style scoped>
.sidebar {
  height: 100vh;
  background: #001529;
  color: white;
}

.logo {
  padding: 16px;
  text-align: center;
  background: rgba(255, 255, 255, 0.1);
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.logo h3 {
  color: white;
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.el-menu-vertical {
  border-right: none;
  background: #001529;
}

.el-menu-vertical .el-menu-item {
  color: rgba(255, 255, 255, 0.65);
}

.el-menu-vertical .el-menu-item:hover {
  background: #1890ff;
  color: white;
}

.el-menu-vertical .el-menu-item.is-active {
  background: #1890ff;
  color: white;
}
</style> 