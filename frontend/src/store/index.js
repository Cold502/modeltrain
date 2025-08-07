import { createStore } from 'vuex'
import model from './modules/model'

export default createStore({
  modules: {
    model
  },
  
  state: {
    user: null,
    isLoggedIn: false,
    models: [],
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
    
    SET_MODELS(state, models) {
      state.models = models
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
    
    logout({ commit }) {
      commit('LOGOUT')
      localStorage.removeItem('user')
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
    },
    
    async loadUserFromStorage({ commit, dispatch }) {
      const userStr = localStorage.getItem('user')
      const token = localStorage.getItem('token')
      const refreshToken = localStorage.getItem('refresh_token')
      
      if (userStr && userStr !== 'undefined' && token && token !== 'undefined') {
        try {
          // 验证token是否有效
          const { authAPI } = await import('../utils/api')
          const response = await authAPI.getCurrentUser()
          const user = response.data
          commit('SET_USER', user)
        } catch (error) {
          console.error('Token验证失败:', error)
          // 如果有refresh token，尝试刷新
          if (refreshToken && refreshToken !== 'undefined') {
            try {
              console.log('🔄 尝试使用refresh token刷新...')
              const { authAPI } = await import('../utils/api')
              const refreshResponse = await authAPI.refreshToken(refreshToken)
              const newToken = refreshResponse.data.access_token
              localStorage.setItem('token', newToken)
              
              // 重新获取用户信息
              const userResponse = await authAPI.getCurrentUser()
              const user = userResponse.data
              commit('SET_USER', user)
              console.log('✅ Token刷新成功')
            } catch (refreshError) {
              console.error('Refresh token也无效:', refreshError)
              // 如果refresh token也无效，清除本地存储
              dispatch('logout')
            }
          } else {
            // 如果token无效，清除本地存储
            dispatch('logout')
          }
        }
      }
      
      const darkMode = localStorage.getItem('darkMode') === 'true'
      commit('SET_DARK_MODE', darkMode)
    },
    
    setModels({ commit }, models) {
      commit('SET_MODELS', models)
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
    availableModels: state => state.models.filter(model => model.status === 'active'),
    recentSessions: state => state.chatSessions.slice(0, 10),
    activeMenu: state => state.activeMenu,
    isDarkMode: state => state.isDarkMode
  }
}) 