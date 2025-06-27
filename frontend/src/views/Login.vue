<template>
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
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { message } from '../utils/message'
import { User, Lock } from '@element-plus/icons-vue'
import { authAPI } from '../utils/api'

export default {
  name: 'Login',
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
        
        const response = await authAPI.login(loginData)
        
        // 保存用户信息到store
        await store.dispatch('login', response.user)
        
        message.success(response.message || '登录成功')
        router.push('/')
        
      } catch (error) {
        // 全局拦截器会处理错误提示，这里留空或只记录日志
        console.error('登录失败:', error);
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
  min-height: 100vh;
  padding: 1.5rem;
  background: linear-gradient(135deg, var(--light-blue) 0%, var(--medium-blue) 50%, var(--primary-blue) 100%);
}

.login-card {
  background: white;
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
  color: #606266;
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
  transition: all 0.3s ease;
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
  transition: all 0.3s ease;
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