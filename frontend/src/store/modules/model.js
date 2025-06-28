import { modelConfigAPI } from '@/utils/api'

const state = {
  modelConfigList: JSON.parse(localStorage.getItem('modelConfigList')) || [],
  selectedModelInfo: JSON.parse(localStorage.getItem('selectedModelInfo')) || null,
  providerList: [],
  availableModels: [],
  loading: false
}

const mutations = {
  SET_MODEL_CONFIG_LIST(state, list) {
    state.modelConfigList = list
    localStorage.setItem('modelConfigList', JSON.stringify(list))
  },
  
  SET_SELECTED_MODEL_INFO(state, modelInfo) {
    state.selectedModelInfo = modelInfo
    localStorage.setItem('selectedModelInfo', JSON.stringify(modelInfo))
  },
  
  SET_PROVIDER_LIST(state, providers) {
    state.providerList = providers
  },
  
  SET_AVAILABLE_MODELS(state, models) {
    state.availableModels = models
  },
  
  SET_LOADING(state, loading) {
    state.loading = loading
  },
  
  ADD_MODEL_CONFIG(state, config) {
    state.modelConfigList.push(config)
    localStorage.setItem('modelConfigList', JSON.stringify(state.modelConfigList))
  },
  
  UPDATE_MODEL_CONFIG(state, updatedConfig) {
    const index = state.modelConfigList.findIndex(config => config.id === updatedConfig.id)
    if (index !== -1) {
      state.modelConfigList.splice(index, 1, updatedConfig)
      localStorage.setItem('modelConfigList', JSON.stringify(state.modelConfigList))
    }
  },
  
  REMOVE_MODEL_CONFIG(state, configId) {
    state.modelConfigList = state.modelConfigList.filter(config => config.id !== configId)
    localStorage.setItem('modelConfigList', JSON.stringify(state.modelConfigList))
  }
}

const actions = {
  // 获取提供商列表
  async fetchProviders({ commit }) {
    try {
      const response = await modelConfigAPI.getProviders()
      commit('SET_PROVIDER_LIST', response.data)
      return response.data
    } catch (error) {
      console.error('获取提供商列表失败:', error)
      throw error
    }
  },
  
  // 获取模型配置列表
  async fetchModelConfigs({ commit }) {
    commit('SET_LOADING', true)
    try {
      const response = await modelConfigAPI.getModels()
      commit('SET_MODEL_CONFIG_LIST', response.data)
      return response.data
    } catch (error) {
      console.error('获取模型配置失败:', error)
      throw error
    } finally {
      commit('SET_LOADING', false)
    }
  },
  
  // 获取提供商的模型列表
  async fetchProviderModels({ commit }, providerId) {
    try {
      if (!providerId) {
        commit('SET_AVAILABLE_MODELS', [])
        return []
      }
      const response = await modelConfigAPI.getAvailableModels(providerId)
      commit('SET_AVAILABLE_MODELS', response.data)
      return response.data
    } catch (error) {
      console.error('获取模型列表失败:', error)
      commit('SET_AVAILABLE_MODELS', [])
      throw error
    }
  },
  
  // 刷新模型列表
  async refreshModels({ commit }, { endpoint, providerId, apiKey }) {
    try {
      const response = await modelConfigAPI.refreshModels({
        endpoint,
        provider_id: providerId,
        api_key: apiKey
      })
      commit('SET_AVAILABLE_MODELS', response.data)
      return response.data
    } catch (error) {
      console.error('刷新模型列表失败:', error)
      throw error
    }
  },
  
  // 保存模型配置
  async saveModelConfig({ commit, dispatch }, { config, isEdit = false }) {
    try {
      let response
      if (isEdit) {
        response = await modelConfigAPI.updateModel(config.id, config)
        commit('UPDATE_MODEL_CONFIG', response.data)
      } else {
        response = await modelConfigAPI.addModel(config)
        commit('ADD_MODEL_CONFIG', response.data)
      }
      
      // 重新获取列表以确保数据同步
      await dispatch('fetchModelConfigs')
      return response.data
    } catch (error) {
      console.error('保存模型配置失败:', error)
      throw error
    }
  },
  
  // 删除模型配置
  async deleteModelConfig({ commit, dispatch }, configId) {
    try {
      await modelConfigAPI.deleteModel(configId)
      commit('REMOVE_MODEL_CONFIG', configId)
      
      // 重新获取列表以确保数据同步
      await dispatch('fetchModelConfigs')
    } catch (error) {
      console.error('删除模型配置失败:', error)
      throw error
    }
  },
  
  // 设置选中的模型
  setSelectedModel({ commit }, modelInfo) {
    commit('SET_SELECTED_MODEL_INFO', modelInfo)
  }
}

const getters = {
  modelConfigList: state => state.modelConfigList,
  selectedModelInfo: state => state.selectedModelInfo,
  providerList: state => state.providerList,
  availableModels: state => state.availableModels,
  loading: state => state.loading,
  
  // 获取可用的模型配置（已配置API Key的）
  availableModelConfigs: state => {
    return state.modelConfigList.filter(config => {
      if (config.providerId?.toLowerCase() === 'ollama') {
        return config.modelName && config.endpoint
      } else {
        return config.modelName && config.endpoint && config.apiKey
      }
    })
  },
  
  // 根据提供商分组模型
  modelsByProvider: (state, getters) => {
    const grouped = {}
    getters.availableModelConfigs.forEach(model => {
      const provider = model.providerName || 'Other'
      if (!grouped[provider]) {
        grouped[provider] = []
      }
      grouped[provider].push(model)
    })
    return grouped
  }
}

export default {
  namespaced: true,
  state,
  mutations,
  actions,
  getters
} 