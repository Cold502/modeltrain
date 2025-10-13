<template>
  <el-container class="app-layout">
    <el-aside width="300px" class="sidebar">
      <el-radio-group v-model="isCollapse" style="margin-bottom: 15px; padding: 10px;">
        <el-radio-button :value="false">展开</el-radio-button>
        <el-radio-button :value="true">折叠</el-radio-button>
      </el-radio-group>

      <el-menu
        :default-active="activeMenu"
        router
        class="sidebar-menu el-menu-vertical-demo"
        :collapse="isCollapse"
        @select="handleMenuSelect"
        @open="handleOpen"
        @close="handleClose"
      >
        <el-menu-item index="/dashboard">
          <el-icon>
            <House/>
          </el-icon>
          <template #title>首页</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/chat">
          <el-icon>
            <ChatDotRound/>
          </el-icon>
          <template #title>模型对话</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/model-test">
          <el-icon>
            <Monitor/>
          </el-icon>
          <template #title>模型测试</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/training">
          <el-icon>
            <Monitor/>
          </el-icon>
          <template #title>模型训练</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/training-viz">
          <el-icon>
            <TrendCharts/>
          </el-icon>
          <template #title>训练可视化</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/prompt-management">
          <el-icon>
            <Document/>
          </el-icon>
          <template #title>系统提示词</template>
        </el-menu-item>

        <el-menu-item index="/dashboard/model-config">
          <el-icon>
            <Coin/>
          </el-icon>
          <template #title>模型配置</template>
        </el-menu-item>

        <el-menu-item v-if="isAdmin" index="/dashboard/admin">
          <el-icon>
            <UserFilled/>
          </el-icon>
          <template #title>用户管理</template>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <el-container>
      <el-header height="70px" class="header">
        <div class="header-left">
          <h1>企业模型训练平台</h1>
        </div>
        <div class="header-right">
          <!-- 黑夜模式切换开关 -->
          <div class="theme-switch" @click="toggleDarkMode">
            <div class="theme-switch-track" :class="{ 'is-dark': isDarkMode }">
              <div class="theme-switch-thumb" :class="{ 'is-dark': isDarkMode }">
                <el-icon v-if="isDarkMode" class="theme-icon">
                  <Moon/>
                </el-icon>
                <el-icon v-else class="theme-icon">
                  <Sunny/>
                </el-icon>
              </div>
            </div>
          </div>

          <el-dropdown @command="handleCommand">
            <span class="user-info">
              <el-avatar :size="36" :src="userAvatar"/>
              <span>{{ userName }}</span>
              <el-icon><ArrowDown/></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="logout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      <el-main class="main-content">
        <router-view/>
      </el-main>
    </el-container>
  </el-container>
</template>

<script>
import {ref, computed, onMounted, watch} from 'vue'
import {useStore} from 'vuex'
import {useRouter, useRoute} from 'vue-router'
import {message} from '../utils/message'
import {
  House,
  ChatDotRound,
  Monitor,
  Setting,
  Document,
  TrendCharts,
  UserFilled,
  ArrowDown,
  Coin,
  Moon,
  Sunny
} from '@element-plus/icons-vue'

export default {
  name: 'Layout',
  components: {
    House,
    ChatDotRound,
    Monitor,
    Setting,
    Document,
    TrendCharts,
    UserFilled,
    ArrowDown,
    Coin,
    Moon,
    Sunny
  },
  setup() {
    const store = useStore()
    const router = useRouter()
    const route = useRoute()
    const isCollapse = ref(false)
    
    const handleOpen = (key, keyPath) => {
      console.log(key, keyPath)
    }
    const handleClose = (key, keyPath) => {
      console.log(key, keyPath)
    }
    
    const userName = computed(() => store.getters.userName)
    const isAdmin = computed(() => store.getters.isAdmin)
    const activeMenu = computed(() => store.getters.activeMenu)
    const isDarkMode = computed(() => store.getters.isDarkMode)
    const userAvatar = computed(() => {
      // 使用本地默认头像，避免外部服务不稳定的问题
      return `/imgs/default-avatar.svg`
    })

    const handleCommand = async (command) => {
      console.log('📋 用户操作:', command)
      if (command === 'logout') {
        try {
          await store.dispatch('logout')
          router.push('/login')
          message.success('已退出登录')
        } catch (error) {
          console.error('登出失败:', error)
          message.error('登出失败，请重试')
        }
      }
    }

    const handleMenuSelect = (index) => {
      console.log('📍 菜单选择:', index)
      store.dispatch('setActiveMenu', index)
    }

    const toggleDarkMode = () => {
      store.dispatch('toggleDarkMode')
    }

    // 监听路由变化，更新菜单状态
    watch(route, (to) => {
      store.dispatch('setActiveMenu', to.path)
    }, {immediate: true})

    onMounted(() => {
      // 确保用户状态正确加载
      store.dispatch('loadUserFromStorage')

      // 设置当前激活菜单
      store.dispatch('setActiveMenu', route.path)
    })

    return {
      userName,
      isAdmin,
      userAvatar,
      activeMenu,
      isDarkMode,
      isCollapse,
      handleCommand,
      handleMenuSelect,
      toggleDarkMode,
      handleOpen,
      handleClose
    }
  }
}
</script>

<style scoped>
.app-layout {
  height: 100vh;
  background: var(--background-blue);
}

.sidebar {
  background: var(--bg-color);
  border-right: 2px solid var(--light-blue);
  box-shadow: 2px 0 8px rgba(100, 168, 219, 0.1);
  overflow: hidden;
}

.sidebar-menu {
  border: none;
  height: calc(100% - 80px);
  background: transparent;
  overflow-y: auto;
  padding: 0.5rem;
}

.sidebar-menu::-webkit-scrollbar {
  width: 4px;
}

.sidebar-menu::-webkit-scrollbar-track {
  background: transparent;
}

.sidebar-menu::-webkit-scrollbar-thumb {
  background: var(--medium-blue);
  border-radius: 2px;
}

.sidebar-menu .el-menu-item {
  margin: 0.3rem 0;
  border-radius: 8px;
  background: transparent;
  color: var(--text-color);
  border: 1px solid transparent;
}

.sidebar-menu .el-menu-item:hover {
  background: var(--light-blue);
  color: var(--dark-blue);
  transform: translateX(4px);
}

.sidebar-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
  color: white;
  box-shadow: 0 2px 8px rgba(100, 168, 219, 0.3);
  border-color: var(--dark-blue);
}

/* 可折叠菜单样式 */
.el-menu-vertical-demo:not(.el-menu--collapse) {
  width: 200px;
  min-height: 400px;
}

.header {
  padding: 0 1.5rem;
  border-bottom: 2px solid var(--light-blue);
  background: var(--bg-color);
  box-shadow: 0 2px 8px rgba(100, 168, 219, 0.1);
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.header-left h1 {
  font-size: 1.6rem;
  font-weight: 700;
  color: var(--dark-blue);
  margin: 0;
  letter-spacing: 1px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  height: 100%;
}

.theme-switch {
  width: 60px;
  height: 30px;
  background: var(--light-blue);
  border-radius: 15px;
  position: relative;
  cursor: pointer;
  border: 2px solid var(--medium-blue);
  flex-shrink: 0;
  align-self: center;
}

.theme-switch:hover {
  transform: scale(1.05);
}

.theme-switch-track {
  width: 100%;
  height: 100%;
  border-radius: 15px;
  position: absolute;
  top: 0;
  left: 0;
}

.theme-switch-track.is-dark {
  background: var(--dark-blue);
}

.theme-switch-thumb {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: white;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 0 1px 0.1px rgba(0, 0, 0, 0.2);
}

.theme-switch-thumb.is-dark {
  transform: translateX(30px) translateY(-50%);
  background: #2c2c2c;
}

.theme-icon {
  font-size: 1rem;
  color: var(--dark-blue);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  color: var(--text-color);
  font-size: 1rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border-radius: 8px;
  background: var(--light-blue);
  border: 1px solid var(--medium-blue);
  height: 40px;
  flex-shrink: 0;
  align-self: center;
}

.user-info:hover {
  background: var(--medium-blue);
  transform: translateY(-1px);
}

.main-content {
  background: var(--background-blue);
  padding: 1.2rem;
  overflow-y: auto;
}
</style> 