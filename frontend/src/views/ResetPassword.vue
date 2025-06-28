<template>
  <div>
    <AuthNavbar />
  <div class="login-container">
    <div class="login-card">
      <div class="login-header">
        <h1>重置密码</h1>
        <p>输入邮箱或昵称以及新密码</p>
      </div>
      
      <el-form
        ref="resetForm"
        :model="resetData"
        :rules="resetRules"
        class="login-form"
        @submit.prevent="handleResetPassword"
      >
        <el-form-item prop="login">
          <el-input
            v-model="resetData.login"
            placeholder="邮箱或昵称"
            size="large"
            :prefix-icon="User"
          />
        </el-form-item>
        
        <el-form-item prop="new_password">
          <el-input
            v-model="resetData.new_password"
            type="password"
            placeholder="新密码"
            size="large"
            :prefix-icon="Lock"
            show-password
          />
        </el-form-item>
        
        <div class="login-actions">
          <el-button
            :loading="loading"
            type="primary"
            size="large"
            style="width: 100%"
            @click="handleResetPassword"
          >
            重置密码
          </el-button>
        </div>
        
        <div class="login-links">
          <el-button type="text" @click="$router.push('/login')">
            返回登录
          </el-button>
        </div>
      </el-form>
    </div>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { message } from '../utils/message'
import { authAPI } from '../utils/api'
import { User, Lock } from '@element-plus/icons-vue'
import AuthNavbar from '../components/AuthNavbar.vue'

export default {
  name: 'ResetPassword',
  components: {
    AuthNavbar
  },
  setup() {
    const router = useRouter()
    const resetForm = ref(null)
    const loading = ref(false)
    
    const resetData = reactive({
      login: '',
      new_password: ''
    })
    
    const resetRules = {
      login: [
        { required: true, message: '请输入邮箱或昵称', trigger: 'blur' }
      ],
      new_password: [
        { required: true, message: '请输入新密码', trigger: 'blur' }
      ]
    }
    
    const handleResetPassword = async () => {
      if (!resetForm.value) return
      
      try {
        await resetForm.value.validate()
        loading.value = true
        
        console.log('开始重置密码，数据:', resetData)
        const response = await authAPI.resetPassword(resetData)
        console.log('重置密码响应:', response)
        
        message.success('密码重置成功，即将跳转到登录页面...')
        
        // 延迟跳转，确保用户看到成功消息
        setTimeout(() => {
          console.log('开始跳转到登录页面')
          router.push('/login').then(() => {
            console.log('跳转成功')
          }).catch((err) => {
            console.error('跳转失败:', err)
          })
        }, 2000)
        
      } catch (error) {
        console.error('重置密码错误:', error)
        if (error.response) {
          message.error(error.response.data.detail || '重置失败')
        } else {
          message.error('网络错误，请重试')
        }
      } finally {
        loading.value = false
      }
    }
    
    return {
      resetForm,
      resetData,
      resetRules,
      loading,
      handleResetPassword,
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