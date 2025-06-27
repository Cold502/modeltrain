<template>
  <div class="reset-container">
    <div class="reset-card">
      <div class="reset-header">
        <h1>重置密码</h1>
        <p>输入邮箱或昵称以及新密码</p>
      </div>
      
      <el-form
        ref="resetForm"
        :model="resetData"
        :rules="resetRules"
        class="reset-form"
      >
        <el-form-item prop="login">
          <el-input
            v-model="resetData.login"
            placeholder="邮箱或昵称"
            size="large"
          />
        </el-form-item>
        
        <el-form-item prop="new_password">
          <el-input
            v-model="resetData.new_password"
            type="password"
            placeholder="新密码"
            size="large"
            show-password
          />
        </el-form-item>
        
        <el-button
          :loading="loading"
          type="primary"
          size="large"
          style="width: 100%"
          @click="handleResetPassword"
        >
          重置密码
        </el-button>
        
        <div class="reset-links">
          <el-button type="text" @click="$router.push('/login')">
            返回登录
          </el-button>
        </div>
      </el-form>
    </div>
  </div>
</template>

<script>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { authAPI } from '../utils/api'

export default {
  name: 'ResetPassword',
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
        { required: true, message: '请输入新密码', trigger: 'blur' },
        { min: 6, message: '密码长度不能少于6位', trigger: 'blur' }
      ]
    }
    
    const handleResetPassword = async () => {
      if (!resetForm.value) return
      
      try {
        await resetForm.value.validate()
        loading.value = true
        
        await authAPI.resetPassword(resetData)
        
        ElMessage.success('密码重置成功，请重新登录')
        router.push('/login')
        
      } catch (error) {
        if (error.response) {
          ElMessage.error(error.response.data.detail || '重置失败')
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
      handleResetPassword
    }
  }
}
</script>

<style scoped>
.reset-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 20px;
}

.reset-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 40px;
  width: 100%;
  max-width: 400px;
}

.reset-header {
  text-align: center;
  margin-bottom: 32px;
}

.reset-header h1 {
  color: #303133;
  margin: 0 0 8px 0;
  font-size: 24px;
  font-weight: 600;
}

.reset-header p {
  color: #909399;
  margin: 0;
  font-size: 14px;
}

.reset-form {
  margin-bottom: 24px;
}

.reset-links {
  text-align: center;
  margin-top: 24px;
}
</style> 