<template>
  <div>
    <AuthNavbar />
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>企业模型训练平台</h1>
        <p>智能化模型训练与管理解决方案</p>
      </div>
      
      <el-form
        ref="loginForm"
        :model="loginData"
        :rules="loginRules"
        class="login-form"
        @submit.prevent="handleLogin"
      >
        <el-form-item prop="login">
          <el-input
            v-model="loginData.login"
            placeholder="邮箱或昵称"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="loginData.password"
            type="password"
            placeholder="密码"
            size="large"
            :prefix-icon="Lock"
            show-password
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        
        <div class="login-actions">
          <el-button
            :loading="loading"
            type="primary"
            size="large"
            style="width: 100%"
            @click="handleLogin"
          >
            登录
          </el-button>
        </div>
        
        <div class="login-links">
          <el-button type="text" @click="$router.push('/reset-password')">
            忘记密码？
          </el-button>
          <el-button type="text" @click="$router.push('/register')">
            注册账号
          </el-button>
        </div>
      </el-form>
      
      <div class="login-footer">
        <p>默认管理员账号：admin / admin</p>
      </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { message } from '../utils/message'
import { User, Lock } from '@element-plus/icons-vue'
import { authAPI } from '../utils/api'
import AuthNavbar from '../components/AuthNavbar.vue'

export default {
  name: 'Login',
  components: {
    AuthNavbar
  },
  setup() {
    const router = useRouter()
    const store = useStore()
    const loginForm = ref(null)
    const loading = ref(false)
    
    const loginData = reactive({
      login: '',
      password: ''
    })
    
    const loginRules = {
      login: [
        { required: true, message: '请输入邮箱或昵称', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' }
      ]
    }
    
    const handleLogin = async () => {
      if (!loginForm.value) return
      
      try {
        await loginForm.value.validate()
        loading.value = true
        
        console.log('🔐 开始登录:', loginData)
        
        // 清除旧的认证信息
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        localStorage.removeItem('refresh_token')
        
        const response = await authAPI.login(loginData)
        console.log('✅ 登录响应:', response.data)
        
        // 保存token到localStorage
        if (response.data.access_token) {
          localStorage.setItem('token', response.data.access_token)
          console.log('🔑 Access Token已保存到localStorage')
        }
        
        // refresh token现在存储在HttpOnly Cookie中，不需要手动保存
        console.log('🔄 Refresh Token已通过HttpOnly Cookie保存')
        
        // 保存用户信息到store
        await store.dispatch('login', response.data.user)
        console.log('💾 用户信息已保存到store:', store.state.user)
        console.log('🔑 登录状态:', store.state.isLoggedIn)
        
        message.success(response.data.message || '登录成功')
        
        // 等待一下确保状态更新完成
        setTimeout(() => {
          console.log('🚀 准备跳转到dashboard')
          console.log('🔍 最终登录状态:', store.state.isLoggedIn)
          console.log('🔍 最终用户信息:', store.state.user)
          router.push('/dashboard')
        }, 100)
        
      } catch (error) {
        console.error('❌ 登录失败:', error)
        // 全局拦截器会处理错误提示，这里留空或只记录日志
      } finally {
        loading.value = false
      }
    }
    
    return {
      loginForm,
      loginData,
      loginRules,
      loading,
      handleLogin,
      User,
      Lock
    }
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 60px);
  margin-top: 60px;
  padding: 1.5rem;
  background: linear-gradient(135deg, var(--light-blue) 0%, var(--medium-blue) 50%, var(--primary-blue) 100%);
}

.login-card {
  background: var(--bg-color);
  border-radius: 20px;
  box-shadow: 0 12px 48px rgba(100, 168, 219, 0.2);
  padding: 3rem 2.5rem;
  width: 100%;
  max-width: 500px;
  border: 2px solid var(--light-blue);
  backdrop-filter: blur(10px);
}

.login-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.login-header h1 {
  font-size: 2.2rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  color: var(--dark-blue);
  letter-spacing: 1px;
}

.login-header p {
  font-size: 1.1rem;
  color: var(--text-color);
  margin: 0;
  font-weight: 400;
}

.login-form {
  margin-bottom: 1.5rem;
}

.login-form .el-form-item {
  margin-bottom: 1.8rem;
}

.login-form .el-input {
  border-radius: 10px;
  height: 48px;
}

.login-form .el-input__wrapper {
  border-radius: 10px;
  border: 2px solid var(--light-blue);
  height: 48px;
  padding: 0 15px;
}

.login-form .el-input__inner {
  font-size: 1rem !important;
  height: 44px;
  line-height: 44px;
}

.login-form .el-input__prefix {
  display: flex;
  align-items: center;
  height: 44px;
}

.login-form .el-input__prefix .el-icon {
  font-size: 1.2rem !important;
  color: var(--primary-blue);
}

.login-form .el-input__wrapper:hover {
  border-color: var(--medium-blue);
}

.login-form .el-input.is-focus .el-input__wrapper {
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(100, 168, 219, 0.1);
}

.login-actions {
  margin: 2rem 0;
}

.login-actions .el-button {
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
  border: none;
  font-weight: 600;
  letter-spacing: 1px;
  height: 48px;
  font-size: 1.1rem;
}

.login-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(100, 168, 219, 0.4);
}

.login-links {
  margin-top: 1.5rem;
  text-align: center;
  display: flex;
  justify-content: space-between;
}

.login-links .el-button {
  font-size: 0.95rem;
  color: var(--primary-blue);
  font-weight: 500;
  padding: 8px 16px;
}

.login-links .el-button:hover {
  color: var(--dark-blue);
}

.login-footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid var(--light-blue);
  text-align: center;
}

.login-footer p {
  font-size: 1rem;
  color: var(--primary-blue);
  margin: 0;
  font-weight: 500;
  background: var(--light-blue);
  padding: 0.8rem 1.5rem;
  border-radius: 10px;
  display: inline-block;
}
</style> 