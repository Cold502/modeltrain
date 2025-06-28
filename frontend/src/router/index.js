import { createRouter, createWebHistory } from 'vue-router'
import store from '../store'

// 页面组件
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import ResetPassword from '../views/ResetPassword.vue'
import Layout from '../components/Layout.vue'
import Dashboard from '../views/Dashboard.vue'
import ModelChat from '../views/ModelChat.vue'
import ModelTest from '../views/ModelTest.vue'
import ModelTraining from '../views/ModelTraining.vue'
import SystemPrompt from '../views/SystemPrompt.vue'
import SwanLabViz from '../views/SwanLabViz.vue'
import AdminPanel from '../views/AdminPanel.vue'
import ModelConfig from '../views/ModelConfig.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue')
  },
  {
    path: '/reset-password',
    name: 'ResetPassword',
    component: () => import('@/views/ResetPassword.vue')
  },
  {
    path: '/dashboard',
    component: Layout,
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        name: 'Dashboard',
        component: Dashboard
      },
      {
        path: 'chat',
        name: 'Chat',
        component: ModelChat
      },
      {
        path: 'training',
        name: 'Training',
        component: ModelTraining
      },
      {
        path: 'training-viz',
        name: 'TrainingViz',
        component: SwanLabViz
      },
      {
        path: 'model-config',
        name: 'ModelConfig',
        component: ModelConfig
      },
      {
        path: 'model-test',
        name: 'ModelTest',
        component: ModelTest
      },
      {
        path: 'prompt-management',
        name: 'PromptManagement',
        component: SystemPrompt
      },
      {
        path: 'admin',
        name: 'AdminPanel',
        component: AdminPanel,
        meta: { requiresAdmin: true }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 简化的路由守卫
router.beforeEach((to, from, next) => {
  console.log('路由跳转:', to.path)
  
  const requiresAuth = to.matched.some(record => record.meta.requiresAuth)
  const requiresAdmin = to.matched.some(record => record.meta.requiresAdmin)
  const isLoggedIn = store.state.isLoggedIn
  const isAdmin = store.getters.isAdmin
  
  console.log('认证状态:', { requiresAuth, isLoggedIn, requiresAdmin, isAdmin })

  if (requiresAuth && !isLoggedIn) {
    console.log('重定向到登录页面')
    next('/login')
  } else if (requiresAdmin && !isAdmin) {
    console.log('权限不足，重定向到首页')
    next('/dashboard')
  } else if ((to.name === 'Login' || to.name === 'Register') && isLoggedIn) {
    console.log('已登录，重定向到首页')
    next('/dashboard')
  } else {
    console.log('路由守卫通过')
    next()
  }
})

export default router 