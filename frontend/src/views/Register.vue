<template>
  <div>
    <AuthNavbar />
    <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <h1>注册账号</h1>
        <p>创建企业模型训练平台账号</p>
      </div>
      
      <el-form
        ref="registerForm"
        :model="registerData"
        :rules="registerRules"
        class="register-form"
      >
        <el-form-item prop="email">
          <el-input
            v-model="registerData.email"
            placeholder="邮箱"
            size="large"
          >
            <template #prefix>
              <el-icon><Message /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="nickname">
          <el-input
            v-model="registerData.nickname"
            placeholder="昵称"
            size="large"
          >
            <template #prefix>
              <el-icon><User /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="registerData.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerData.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            show-password
          >
            <template #prefix>
              <el-icon><Lock /></el-icon>
            </template>
          </el-input>
        </el-form-item>
        
        <div class="register-actions">
          <el-button
            :loading="loading"
            type="primary"
            size="large"
            style="width: 100%"
            @click="handleRegister"
          >
            注册
          </el-button>
        </div>
        
        <div class="register-links">
          <el-button type="text" @click="$router.push('/login')">
            已有账号？立即登录
          </el-button>
        </div>
      </el-form>
      
      <div class="register-footer">
        <p>企业级AI模型训练平台</p>
      </div>
    </div>
  </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from '../utils/message'
import { authAPI } from '../utils/api'
import { User, Lock, Message } from '@element-plus/icons-vue'
import AuthNavbar from '../components/AuthNavbar.vue'

export default {
  name: 'Register',
  components: {
    User,
    Lock,
    Message,
    AuthNavbar
  },
  setup() {
    const router = useRouter()
    const registerForm = ref(null)
    const loading = ref(false)
    
    const registerData = reactive({
      email: '',
      nickname: '',
      password: '',
      confirmPassword: ''
    })
    
    const validatePassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请输入密码'))
      } else {
        callback()
      }
    }
    
    const validateConfirmPassword = (rule, value, callback) => {
      if (value === '') {
        callback(new Error('请确认密码'))
      } else if (value !== registerData.password) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }
    
    const registerRules = {
      email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '请输入正确的邮箱格式', trigger: ['blur', 'change'] }
      ],
      nickname: [
        { required: true, message: '请输入昵称', trigger: 'blur' }
      ],
      password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { validator: validatePassword, trigger: 'blur' }
      ],
      confirmPassword: [
        { required: true, message: '请再次输入密码', trigger: 'blur' },
        { validator: validateConfirmPassword, trigger: 'blur' }
      ]
    }
    
    const handleRegister = async () => {
      if (!registerForm.value) return
      
      try {
        await registerForm.value.validate()
        loading.value = true
        
        await authAPI.register(registerData)
        
        message.success('注册成功！正在跳转到登录页面...')
        setTimeout(() => {
          router.push('/login')
        }, 2000)
        
      } catch (error) {
        // 全局拦截器会处理错误提示，这里留空或只记录日志
        console.error('注册失败:', error)
      } finally {
        loading.value = false
      }
    }
    
    return {
      registerForm,
      registerData,
      registerRules,
      loading,
      handleRegister,
      User,
      Lock,
      Message
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: calc(100vh - 60px);
  margin-top: 60px;
  padding: 1.5rem;
  background: linear-gradient(135deg, var(--light-blue) 0%, var(--medium-blue) 50%, var(--primary-blue) 100%);
}

.register-card {
  background: var(--bg-color);
  border-radius: 20px;
  box-shadow: 0 12px 48px rgba(100, 168, 219, 0.2);
  padding: 3rem 2.5rem;
  width: 100%;
  max-width: 500px;
  border: 2px solid var(--light-blue);
  backdrop-filter: blur(10px);
}

.register-header {
  text-align: center;
  margin-bottom: 2.5rem;
}

.register-header h1 {
  font-size: 2.2rem;
  font-weight: 700;
  margin: 0 0 1rem 0;
  color: var(--dark-blue);
  letter-spacing: 1px;
}

.register-header p {
  font-size: 1.1rem;
  color: var(--text-color);
  margin: 0;
  font-weight: 400;
}

.register-form {
  margin-bottom: 1.5rem;
}

.register-form .el-form-item {
  margin-bottom: 1.8rem;
}

.register-form .el-input {
  border-radius: 10px;
  height: 48px;
}

.register-form .el-input__wrapper {
  border-radius: 10px;
  border: 2px solid var(--light-blue);
  transition: all 0.3s ease;
  height: 48px;
  padding: 0 15px;
}

.register-form .el-input__inner {
  font-size: 1rem !important;
  height: 44px;
  line-height: 44px;
}

.register-form .el-input__prefix {
  display: flex;
  align-items: center;
  height: 44px;
}

.register-form .el-input__prefix .el-icon {
  font-size: 1.2rem !important;
  color: var(--primary-blue);
}

.register-form .el-input__wrapper:hover {
  border-color: var(--medium-blue);
}

.register-form .el-input.is-focus .el-input__wrapper {
  border-color: var(--primary-blue);
  box-shadow: 0 0 0 3px rgba(100, 168, 219, 0.1);
}

.register-actions {
  margin: 2rem 0;
}

.register-actions .el-button {
  border-radius: 10px;
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
  border: none;
  font-weight: 600;
  letter-spacing: 1px;
  transition: all 0.3s ease;
  height: 48px;
  font-size: 1.1rem;
}

.register-actions .el-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(100, 168, 219, 0.4);
}

.register-links {
  margin-top: 1.5rem;
  text-align: center;
}

.register-links .el-button {
  font-size: 0.95rem;
  color: var(--primary-blue);
  font-weight: 500;
  padding: 8px 16px;
}

.register-links .el-button:hover {
  color: var(--dark-blue);
}

.register-footer {
  margin-top: 2rem;
  padding-top: 1.5rem;
  border-top: 2px solid var(--light-blue);
  text-align: center;
}

.register-footer p {
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