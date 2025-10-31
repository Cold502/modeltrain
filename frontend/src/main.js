// 第1行：从 Vue 导入 createApp 方法
import { createApp } from 'vue'

// 第2行：导入根组件 App.vue
import App from './App.vue'

// 第3-4行：导入路由和 Vuex store
import router from './router'      // 路由配置
import store from './store'        // ← Vuex store 从 ./store/index.js 导入

// 第5-8行：导入 Element Plus UI 库和全局样式
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import * as ElementPlusIconsVue from '@element-plus/icons-vue'
import './assets/styles/main.css'

// 第11行：创建 Vue 应用实例（app 就是你的整个应用）
const app = createApp(App)  // ← app 就是 Vue 应用实例
// createApp(App) 创建一个 Vue 应用，App 是根组件

// 第14-16行：注册所有 Element Plus 图标为全局组件
for (const [key, component] of Object.entries(ElementPlusIconsVue)) {
  app.component(key, component)  // 注册图标组件
}

// 第18-20行：注册插件（这里就是注册的地方！）
app.use(store)        // ← 注册 Vuex store（在这里！）
app.use(router)       // 注册 Vue Router
app.use(ElementPlus)  // 注册 Element Plus

// 第22-24行：初始化并挂载应用
store.dispatch('loadUserFromStorage').then(() => {
  app.mount('#app')  // 将 Vue 应用挂载到 HTML 中的 <div id="app"> 元素
})