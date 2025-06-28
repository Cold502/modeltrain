<template>
  <div class="admin-panel">
    <div class="page-header">
      <h2>用户管理</h2>
      <p>管理系统用户和权限</p>
    </div>
    
    <!-- 系统统计卡片 -->
    <div class="stats-section">
      <div class="stat-card">
        <div class="stat-icon">
          <el-icon><User /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.users?.total || 0 }}</div>
          <div class="stat-label">总用户数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon active">
          <el-icon><UserFilled /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.users?.active || 0 }}</div>
          <div class="stat-label">活跃用户</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon admin">
          <el-icon><Avatar /></el-icon>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stats.users?.admins || 0 }}</div>
          <div class="stat-label">管理员数</div>
        </div>
      </div>
    </div>

    <!-- 用户列表 -->
    <div class="users-section">
      <div class="section-header">
        <h3>用户列表</h3>
        <el-button 
          type="primary" 
          @click="loadUsers"
          :loading="loading"
          class="refresh-btn"
        >
          <el-icon><Refresh /></el-icon>
          刷新
        </el-button>
      </div>
      
      <div class="table-container">
        <el-table 
          :data="users" 
          v-loading="loading"
          class="users-table"
          :header-cell-style="{ background: 'var(--light-blue)', color: 'var(--text-color)' }"
          table-layout="auto"
          style="width: 100%"
        >
          <el-table-column prop="id" label="ID" width="80" />
          <el-table-column prop="nickname" label="昵称" min-width="120" />
          <el-table-column prop="email" label="邮箱" min-width="200" />
          <el-table-column label="状态" width="100">
            <template #default="scope">
              <el-tag 
                :type="scope.row.is_active ? 'success' : 'danger'"
                class="status-tag"
              >
                {{ scope.row.is_active ? '活跃' : '禁用' }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column label="角色" width="180">
            <template #default="scope">
              <div class="role-cell">
                <el-tag 
                  :type="scope.row.is_admin ? 'warning' : 'primary'"
                  class="role-tag"
                >
                  {{ scope.row.is_admin ? '管理员' : '普通用户' }}
                </el-tag>
                <el-tooltip
                  v-if="scope.row.nickname !== 'admin' && scope.row.id !== currentUserId"
                  :content="scope.row.is_admin ? '设为普通用户' : '设为管理员'"
                  placement="top"
                >
                  <el-button
                    type="primary"
                    size="small"
                    @click="toggleUserRole(scope.row)"
                    class="role-toggle-btn"
                    circle
                  >
                    <el-icon><Switch /></el-icon>
                  </el-button>
                </el-tooltip>
              </div>
            </template>
          </el-table-column>
          <el-table-column prop="created_at" label="注册时间" min-width="180">
            <template #default="scope">
              {{ formatTime(scope.row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column label="操作" width="150" fixed="right">
            <template #default="scope">
              <el-tooltip
                v-if="scope.row.nickname !== 'admin' && scope.row.id !== currentUserId"
                content="删除用户"
                placement="top"
              >
                <el-button
                  type="danger"
                  size="small"
                  @click="deleteUser(scope.row)"
                  class="delete-btn"
                  circle
                >
                  <el-icon><Delete /></el-icon>
                </el-button>
              </el-tooltip>
              <span v-else class="no-action">—</span>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useStore } from 'vuex'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminAPI } from '../utils/api'
import { message } from '../utils/message'
import { 
  User, 
  UserFilled, 
  Avatar, 
  Refresh, 
  Switch, 
  Delete 
} from '@element-plus/icons-vue'

export default {
  name: 'AdminPanel',
  components: {
    User,
    UserFilled,
    Avatar,
    Refresh,
    Switch,
    Delete
  },
  setup() {
    const store = useStore()
    const users = ref([])
    const stats = ref({})
    const loading = ref(false)
    
    const currentUserId = computed(() => store.state.user?.id)
    
    const formatTime = (timeStr) => {
      const date = new Date(timeStr)
      return date.toLocaleString('zh-CN')
    }
    
    const loadUsers = async () => {
      loading.value = true
      try {
        const [usersResponse, statsResponse] = await Promise.all([
          adminAPI.getAllUsers(),
          adminAPI.getAdminStats()
        ])
        
        users.value = usersResponse.data || []
        stats.value = statsResponse.data || {}
      } catch (error) {
        console.error('加载用户数据失败:', error)
        message.error('加载用户数据失败')
      } finally {
        loading.value = false
      }
    }
    
    const deleteUser = async (user) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除用户 "${user.nickname}" 吗？`,
          '确认删除',
          { 
            type: 'warning',
            confirmButtonText: '确定删除',
            cancelButtonText: '取消'
          }
        )
        
        await adminAPI.deleteUser(user.id)
        
        message.success('删除成功')
        loadUsers()
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('删除用户失败:', error)
          message.error('删除用户失败')
        }
      }
    }
    
    const toggleUserRole = async (user) => {
      const newRole = !user.is_admin
      const roleText = newRole ? '管理员' : '普通用户'
      
      try {
        await ElMessageBox.confirm(
          `确定要将用户 "${user.nickname}" 的角色修改为 "${roleText}" 吗？`,
          '确认修改角色',
          { 
            type: 'warning',
            confirmButtonText: '确定修改',
            cancelButtonText: '取消'
          }
        )
        
        await adminAPI.updateUserRole(user.id, newRole)
        
        message.success(`用户角色已修改为${roleText}`)
        loadUsers()
        
      } catch (error) {
        if (error !== 'cancel') {
          console.error('修改用户角色失败:', error)
          message.error('修改用户角色失败')
        }
      }
    }
    
    onMounted(() => {
      loadUsers()
    })
    
    return {
      users,
      stats,
      loading,
      currentUserId,
      formatTime,
      loadUsers,
      deleteUser,
      toggleUserRole
    }
  }
}
</script>

<style scoped>
.admin-panel {
  padding: 2rem;
  background: var(--background-blue);
  min-height: 100vh;
}

.page-header {
  margin-bottom: 3rem;
}

.page-header h2 {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-color);
  margin: 0 0 1rem 0;
}

.page-header p {
  font-size: 1.2rem;
  color: var(--primary-blue);
  margin: 0;
}

/* 统计卡片区域 */
.stats-section {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
  margin-bottom: 3rem;
}

.stat-card {
  background: var(--card-bg);
  border: 2px solid var(--border-color);
  border-radius: 16px;
  padding: 2rem;
  display: flex;
  align-items: center;
  gap: 1.5rem;
  box-shadow: 0 4px 16px rgba(100, 168, 219, 0.1);
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(100, 168, 219, 0.2);
}

.stat-icon {
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: var(--light-blue);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.8rem;
  color: var(--primary-blue);
}

.stat-icon.active {
  background: linear-gradient(135deg, #4ade80, #22c55e);
  color: white;
}

.stat-icon.admin {
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: white;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 2.5rem;
  font-weight: 700;
  color: var(--text-color);
  line-height: 1;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1.1rem;
  color: var(--primary-blue);
  font-weight: 500;
}

/* 用户列表区域 */
.users-section {
  background: var(--card-bg);
  border: 2px solid var(--border-color);
  border-radius: 16px;
  overflow: hidden;
  box-shadow: 0 4px 16px rgba(100, 168, 219, 0.1);
}

.section-header {
  padding: 2rem;
  border-bottom: 2px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--bg-color);
}

.section-header h3 {
  font-size: 1.6rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.refresh-btn {
  height: 48px;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 12px;
  background: linear-gradient(135deg, var(--primary-blue), var(--dark-blue));
  border: none;
  box-shadow: 0 4px 12px rgba(100, 168, 219, 0.3);

}

.refresh-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 20px rgba(100, 168, 219, 0.4);
}

.table-container {
  padding: 2rem;
  background: var(--bg-color);
}

.users-table {
  width: 100%;
}

.users-table :deep(.el-table td) {
  font-size: 1.1rem;
  padding: 1rem 0.8rem;
}

.users-table :deep(.el-table th) {
  font-size: 1.2rem;
  font-weight: 600;
  padding: 1.2rem 0.8rem;
}

/* 彻底禁用表格的所有hover效果 */
.dark-mode .users-table :deep(.el-table__body tr:hover),
.dark-mode .users-table :deep(.el-table__body tr:hover > td),
.dark-mode .users-table :deep(.el-table__body tr:hover > td.el-table__cell),
.dark-mode .users-table :deep(.el-table__body tr.hover-row),
.dark-mode .users-table :deep(.el-table__body tr.hover-row > td),
.dark-mode .users-table :deep(.el-table__body tr.hover-row > td.el-table__cell) {
  background-color: rgba(90, 155, 212, 0.08) !important;
  background: rgba(90, 155, 212, 0.08) !important;
}

.status-tag, .role-tag {
  font-size: 1rem;
  font-weight: 500;
  padding: 0.3rem 0.8rem;
  border-radius: 8px;
}

.role-cell {
  display: flex;
  align-items: center;
  gap: 1rem;
  justify-content: flex-start;
}

.role-toggle-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  font-size: 1rem;
  background: var(--primary-blue);
  border: none;
  color: white;
}

.role-toggle-btn:hover {
  background: var(--dark-blue);
  transform: scale(1.1);
}

.delete-btn {
  width: 36px;
  height: 36px;
  padding: 0;
  font-size: 1.1rem;
  background: #ef4444;
  border: none;
  color: white;
}

.delete-btn:hover {
  background: #dc2626;
  transform: scale(1.1);
}

.no-action {
  color: var(--text-color);
  opacity: 0.5;
  font-size: 1.2rem;
}

/* 黑夜模式适配 */
:deep(.el-tag) {
  border: 1px solid var(--border-color);
}

:deep(.el-button--text) {
  color: var(--primary-blue);
}

:deep(.el-button--text:hover) {
  color: var(--dark-blue);
}

:deep(.el-loading-mask) {
  background: rgba(0, 0, 0, 0.3);
}
</style> 