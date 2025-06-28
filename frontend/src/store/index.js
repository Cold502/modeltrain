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
    },
    
    loadUserFromStorage({ commit }) {
      const userStr = localStorage.getItem('user')
      if (userStr && userStr !== 'undefined') {
        const user = JSON.parse(userStr)
        commit('SET_USER', user)
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