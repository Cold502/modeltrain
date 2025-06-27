<template>
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
          />
        </el-form-item>
        
        <el-form-item prop="nickname">
          <el-input
            v-model="registerData.nickname"
            placeholder="昵称"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="password">
          <el-input
            v-model="registerData.password"
            type="password"
            placeholder="密码"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-form-item prop="confirmPassword">
          <el-input
            v-model="registerData.confirmPassword"
            type="password"
            placeholder="确认密码"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-button
          :loading="loading"
          type="primary"
          size="large"
          style="width: 100%"
          @click="handleRegister"
        >
          注册
        </el-button>
        
        <div class="register-links">
          <el-button type="text" @click="$router.push('/login')">
            已有账号？立即登录
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { message } from '../utils/message'
import { authAPI } from '../utils/api'

export default {
  name: 'Register',
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
      handleRegister
    }
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.register-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.register-header h1 {
  color: #303133;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.register-header p {
  color: #909399;
  margin: 0;
  font-size: 14px;
}

.register-form {
  margin-bottom: 24px;
}

.register-links {
  text-align: center;
  margin-top: 24px;
}
</style> 