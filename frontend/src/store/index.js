import { createStore } from 'vuex'
import model from './modules/model'

export default createStore({
  modules: {
    model
  },
  
  state: {
    user: null,
    isLoggedIn: false,
    chatSessions: [],
    currentSession: null,
    activeMenu: '/',
    isDarkMode: false
  },
  
  mutations: {
    SET_USER(state, user) {
      state.user = user
      state.isLoggedIn = !!user
    },
    
    LOGOUT(state) {
      state.user = null
      state.isLoggedIn = false
      state.chatSessions = []
      state.currentSession = null
    },
    
    
    SET_CHAT_SESSIONS(state, sessions) {
      state.chatSessions = sessions
    },
    
    SET_CURRENT_SESSION(state, session) {
      state.currentSession = session
    },
    
    ADD_MESSAGE(state, message) {
      if (state.currentSession) {
        if (!state.currentSession.messages) {
          state.currentSession.messages = []
        }
        state.currentSession.messages.push(message)
      }
    },
    
    SET_ACTIVE_MENU(state, path) {
      state.activeMenu = path
    },
    
    SET_DARK_MODE(state, isDark) {
      state.isDarkMode = isDark
      localStorage.setItem('darkMode', isDark.toString())
      if (isDark) {
        document.documentElement.classList.add('dark-mode')
      } else {
        document.documentElement.classList.remove('dark-mode')
      }
    }
  },
  
  actions: {
    login({ commit }, user) {
      commit('SET_USER', user)
      localStorage.setItem('user', JSON.stringify(user))
    },
    
    async logout({ commit }) {
      try {
        // 调用后端登出API清除cookie
        const { authAPI } = await import('../utils/api')
        await authAPI.logout()
      } catch (error) {
        console.error('登出API调用失败:', error)
      } finally {
        commit('LOGOUT')
        localStorage.removeItem('user')
        localStorage.removeItem('token')
        // 注意：refresh_token存储在HttpOnly Cookie中，不需要手动清除localStorage
        console.log('✅ 用户登出，本地存储已清除')
      }
    },
    
    async loadUserFromStorage({ commit, dispatch }) {
      const userStr = localStorage.getItem('user')
      const token = localStorage.getItem('token')
      
      if (userStr && userStr !== 'undefined' && token && token !== 'undefined') {
        try {
          // 验证token是否有效
          const { authAPI } = await import('../utils/api')
          const response = await authAPI.getCurrentUser()
          const user = response.data
          commit('SET_USER', user)
          console.log('✅ 从存储中加载用户成功:', user)
        } catch (error) {
          console.error('❌ Token验证失败:', error)
          // 如果token无效，清除本地存储并跳转到登录页
          console.log('🔄 清除无效的本地存储')
          commit('LOGOUT')
          localStorage.removeItem('user')
          localStorage.removeItem('token')
          // 注意：refresh_token存储在HttpOnly Cookie中，不需要手动清除localStorage
          
          // 如果当前不在登录页，跳转到登录页
          const currentRoute = window.location.pathname
          if (currentRoute !== '/login' && currentRoute !== '/register' && currentRoute !== '/reset-password') {
            console.log('🔄 跳转到登录页')
            window.location.href = '/login'
          }
        }
      } else {
        console.log('📱 本地存储中没有有效的用户信息')
        // 清除可能存在的无效数据
        localStorage.removeItem('user')
        localStorage.removeItem('token')
        // 注意：refresh_token存储在HttpOnly Cookie中，不需要手动清除localStorage
      }
      
      const darkMode = localStorage.getItem('darkMode') === 'true'
      commit('SET_DARK_MODE', darkMode)
    },
    
    
    setChatSessions({ commit }, sessions) {
      commit('SET_CHAT_SESSIONS', sessions)
    },
    
    setCurrentSession({ commit }, session) {
      commit('SET_CURRENT_SESSION', session)
    },
    
    addMessage({ commit }, message) {
      commit('ADD_MESSAGE', message)
    },
    
    setActiveMenu({ commit }, path) {
      commit('SET_ACTIVE_MENU', path)
    },
    
    toggleDarkMode({ commit, state }) {
      commit('SET_DARK_MODE', !state.isDarkMode)
    }
  },
  
  getters: {
    isAdmin: state => state.user && state.user.is_admin,
    userName: state => state.user ? state.user.nickname : '',
    recentSessions: state => state.chatSessions.slice(0, 10),
    activeMenu: state => state.activeMenu,
    isDarkMode: state => state.isDarkMode
  }
}) 