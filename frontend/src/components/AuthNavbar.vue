<template>
  <div class="auth-navbar">
    <div class="navbar-content">
      <div class="navbar-left">
        <h2>企业模型训练平台</h2>
      </div>
      
      <div class="navbar-right">
        <!-- 主题切换开关 -->
        <div class="theme-switch" @click="toggleDarkMode">
          <div class="theme-switch-track" :class="{ 'is-dark': isDarkMode }">
            <div class="theme-switch-thumb" :class="{ 'is-dark': isDarkMode }">
              <el-icon v-if="isDarkMode" class="theme-icon"><Moon /></el-icon>
              <el-icon v-else class="theme-icon"><Sunny /></el-icon>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useStore } from 'vuex'
import { Moon, Sunny } from '@element-plus/icons-vue'

export default {
  name: 'AuthNavbar',
  components: {
    Moon,
    Sunny
  },
  setup() {
    const store = useStore()
    
    const isDarkMode = computed(() => store.getters.isDarkMode)
    
    const toggleDarkMode = () => {
      store.dispatch('toggleDarkMode')
    }
    
    return {
      isDarkMode,
      toggleDarkMode
    }
  }
}
</script>

<style scoped>
.auth-navbar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  height: 60px;
  background: var(--bg-color);
  border-bottom: 2px solid var(--light-blue);
  box-shadow: 0 2px 8px rgba(100, 168, 219, 0.1);
  z-index: 1000;
}

.navbar-content {
  height: 100%;
  padding: 0 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  max-width: 1200px;
  margin: 0 auto;
}

.navbar-left h2 {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--dark-blue);
  margin: 0;
  letter-spacing: 1px;
}

.navbar-right {
  display: flex;
  align-items: center;
}

.theme-switch {
  width: 50px;
  height: 26px;
  background: var(--light-blue);
  border-radius: 13px;
  position: relative;
  cursor: pointer;
  border: 2px solid var(--medium-blue);
}

.theme-switch:hover {
  transform: scale(1.05);
}

.theme-switch-track {
  width: 100%;
  height: 100%;
  border-radius: 13px;
  position: absolute;
  top: 0;
  left: 0;
}

.theme-switch-track.is-dark {
  background: var(--dark-blue);
}

.theme-switch-thumb {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  background: white;
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.theme-switch-thumb.is-dark {
  transform: translateX(24px) translateY(-50%);
  background: #2c2c2c;
}

.theme-icon {
  font-size: 0.9rem;
  color: var(--dark-blue);
}

.theme-switch-thumb.is-dark .theme-icon {
  color: #ffd700;
}
</style> 