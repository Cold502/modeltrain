# Vuex 从零开始教程

> 面向完全不懂 Vuex 的初学者，用最简单的语言讲清楚 Vuex 是什么、为什么要用、怎么用。

---

## 🎯 第一章：为什么需要 Vuex？

### 没有 Vuex 的痛苦

假设你在做一个购物网站，有这些组件：

```
App.vue
├── Header.vue          （显示用户名、购物车数量）
├── ProductList.vue     （商品列表）
│   └── ProductItem.vue （单个商品，点击加入购物车）
└── ShoppingCart.vue    （购物车）
```

**问题来了**：当用户点击"加入购物车"，怎么让 Header 显示新的购物车数量？

#### 方法1：层层传递（Props 地狱）

```vue
<!-- ❌ 太痛苦了！ -->
<template>
  <!-- App.vue 要把 cartCount 传给 Header -->
  <Header :cartCount="cartCount" />
  
  <!-- 还要把更新函数传给 ProductList -->
  <ProductList @add-to-cart="addToCart" />
</template>

<script>
export default {
  data() {
    return {
      cartCount: 0  // 数据在最顶层
    }
  },
  methods: {
    addToCart() {
      this.cartCount++
      // 还要通知其他组件...
    }
  }
}
</script>
```

**问题**：
- 🤯 层级多了，传来传去很麻烦
- 🐛 容易出 bug（忘记传某个 prop）
- 😫 代码难维护

#### 方法2：用 Vuex（优雅！）

```vue
<!-- ✅ 任何组件都能直接访问购物车数量 -->
<template>
  <div>购物车: {{ $store.state.cartCount }}</div>
  <button @click="$store.commit('ADD_TO_CART')">加入购物车</button>
</template>
```

**优势**：
- ✅ 任何组件都能直接读取数据
- ✅ 任何组件都能直接修改数据（通过规定的方式）
- ✅ 不需要层层传递

---

## 🏪 第二章：Vuex 是什么？（用超市来理解）

**Vuex 就是一个"全局数据仓库"**，类似超市：

```
🏪 Vuex Store（超市）
├── 📦 State        → 货架（存放商品/数据）
├── 👀 Getters      → 查价员（帮你查询、计算）
├── 💰 Mutations    → 收银员（唯一能改库存的人）
└── 🚚 Actions      → 进货流程（可以包含复杂操作）
```

### 完整类比

| Vuex 概念 | 超市角色 | 作用 | 是否异步 |
|-----------|----------|------|----------|
| **State** | 货架 | 存放商品（数据） | - |
| **Getters** | 查价员 | 查询商品信息 | - |
| **Mutations** | 收银员 | 修改库存（必须同步） | ❌ 必须同步 |
| **Actions** | 进货流程 | 复杂业务（可以异步） | ✅ 可以异步 |

### 规则

1. **顾客**（组件）想买东西，不能直接拿货架上的商品改标签
2. 必须通过**收银员**（Mutation）结账，收银员会修改库存
3. 如果要进货，要走**进货流程**（Action），最后还是收银员改库存
4. 想查价格？找**查价员**（Getter）

---

## 📝 第三章：手把手创建第一个 Vuex Store

### 步骤1：安装 Vuex

```bash
npm install vuex@next
```

### 步骤2：创建 Store 文件

在 `src/store/index.js` 创建文件：

```js
import { createStore } from 'vuex'

// 创建一个超市
const store = createStore({
  // 1. State = 货架（存数据）
  state: {
    count: 0,           // 计数器
    username: '游客',    // 用户名
    cartItems: []       // 购物车
  },

  // 2. Getters = 查价员（查询、计算）
  getters: {
    // 获取当前计数（简单查询）
    currentCount: state => state.count,
    
    // 计算购物车总数（复杂计算）
    cartTotal: state => {
      return state.cartItems.reduce((sum, item) => sum + item.price, 0)
    },
    
    // 判断是否登录
    isLoggedIn: state => state.username !== '游客'
  },

  // 3. Mutations = 收银员（修改数据，必须同步）
  mutations: {
    // 增加计数
    INCREMENT(state) {
      state.count++
    },
    
    // 设置用户名
    SET_USERNAME(state, newName) {
      state.username = newName
    },
    
    // 添加商品到购物车
    ADD_TO_CART(state, product) {
      state.cartItems.push(product)
    }
  },

  // 4. Actions = 进货流程（处理复杂逻辑，可以异步）
  actions: {
    // 简单操作：直接调用 mutation
    increment({ commit }) {
      commit('INCREMENT')
    },
    
    // 复杂操作：先登录（异步），再设置用户名
    async login({ commit }, { username, password }) {
      // 模拟调用登录 API（异步）
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify({ username, password })
      })
      
      const data = await response.json()
      
      // 登录成功后，调用 mutation 修改状态
      commit('SET_USERNAME', data.username)
    }
  }
})

export default store
```

### 步骤3：在 Vue 应用中注册

在 `src/main.js` 中：

```js
import { createApp } from 'vue'
import App from './App.vue'
import store from './store'  // 导入 store

const app = createApp(App)

app.use(store)  // 注册到 Vue 应用

app.mount('#app')
```

**注册后，所有组件都能通过 `this.$store` 或 `useStore()` 访问 store！**

---

## 🎮 第四章：在组件中使用 Vuex

### 方式1：在 `<template>` 中直接使用

```vue
<template>
  <div>
    <!-- 读取 state -->
    <p>当前计数: {{ $store.state.count }}</p>
    <p>用户名: {{ $store.state.username }}</p>
    
    <!-- 读取 getter -->
    <p>购物车总价: {{ $store.getters.cartTotal }}</p>
    
    <!-- 调用 mutation -->
    <button @click="$store.commit('INCREMENT')">+1</button>
    
    <!-- 调用 action -->
    <button @click="$store.dispatch('increment')">+1（通过Action）</button>
  </div>
</template>
```

### 方式2：在 `<script>` 中使用（推荐）

```vue
<template>
  <div>
    <p>计数: {{ count }}</p>
    <p>用户: {{ username }}</p>
    <p>是否登录: {{ isLoggedIn }}</p>
    
    <button @click="handleIncrement">+1</button>
    <button @click="handleLogin">登录</button>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'

// 获取 store
const store = useStore()

// 📖 读取 state（需要用 computed 包装，保持响应式）
const count = computed(() => store.state.count)
const username = computed(() => store.state.username)

// 📖 读取 getter
const isLoggedIn = computed(() => store.getters.isLoggedIn)

// ✏️ 调用 mutation
const handleIncrement = () => {
  store.commit('INCREMENT')
}

// ✏️ 调用 action
const handleLogin = async () => {
  await store.dispatch('login', {
    username: 'admin',
    password: '123456'
  })
}
</script>
```

---

## 🔑 第五章：四大核心概念详解

### 1️⃣ State（数据仓库）

**作用**：存储所有共享数据

```js
state: {
  count: 0,
  user: null,
  isLoading: false,
  todos: []
}
```

**访问方式**：

```js
// 方式1：直接访问
store.state.count

// 方式2：在组件中（推荐用 computed）
const count = computed(() => store.state.count)

// 方式3：在模板中
{{ $store.state.count }}
```

**注意**：
- ❌ **不要直接修改** `store.state.count = 10`
- ✅ **通过 mutation 修改** `store.commit('SET_COUNT', 10)`

---

### 2️⃣ Getters（计算属性）

**作用**：基于 state 计算派生数据，类似组件的 `computed`

```js
getters: {
  // 简单getter：直接返回 state
  count: state => state.count,
  
  // 计算getter：基于 state 计算新值
  doubleCount: state => state.count * 2,
  
  // 过滤getter：筛选数据
  doneTodos: state => {
    return state.todos.filter(todo => todo.done)
  },
  
  // 依赖其他getter
  doneTodosCount: (state, getters) => {
    return getters.doneTodos.length
  },
  
  // 返回函数（支持传参）
  getTodoById: state => id => {
    return state.todos.find(todo => todo.id === id)
  }
}
```

**使用方式**：

```js
// 普通 getter
store.getters.count         // 0
store.getters.doubleCount   // 0

// 带参数的 getter
store.getters.getTodoById(1)  // { id: 1, text: '...', done: false }
```

**为什么要用 Getter？**

```js
// ❌ 不用 getter：每个组件都要写一遍计算逻辑
computed: {
  doneTodos() {
    return this.$store.state.todos.filter(todo => todo.done)
  }
}

// ✅ 用 getter：只需定义一次，到处使用
const doneTodos = computed(() => store.getters.doneTodos)
```

---

### 3️⃣ Mutations（状态修改器）

**作用**：**唯一**能修改 state 的地方，必须是同步函数

```js
mutations: {
  // 基本格式：MUTATION_NAME(state, payload)
  INCREMENT(state) {
    state.count++
  },
  
  // 带参数的 mutation
  SET_COUNT(state, newCount) {
    state.count = newCount
  },
  
  // 多个参数：用对象传递
  ADD_TODO(state, { id, text }) {
    state.todos.push({ id, text, done: false })
  },
  
  // 修改复杂数据
  UPDATE_USER(state, user) {
    state.user = { ...state.user, ...user }
  }
}
```

**调用方式**：

```js
// 方式1：不带参数
store.commit('INCREMENT')

// 方式2：带一个参数
store.commit('SET_COUNT', 10)

// 方式3：带多个参数（用对象）
store.commit('ADD_TODO', {
  id: 1,
  text: '学习 Vuex'
})

// 方式4：对象风格（推荐）
store.commit({
  type: 'ADD_TODO',
  id: 1,
  text: '学习 Vuex'
})
```

**为什么 Mutation 必须是同步的？**

```js
// ❌ 错误：mutation 中使用异步
mutations: {
  async FETCH_USER(state) {
    const user = await fetch('/api/user')  // ❌ 不允许！
    state.user = user
  }
}

// 问题：Vuex DevTools 无法准确记录状态变化的时机

// ✅ 正确：异步操作放在 action 中
actions: {
  async fetchUser({ commit }) {
    const user = await fetch('/api/user')  // ✅ 可以异步
    commit('SET_USER', user)  // ✅ 同步提交
  }
}
```

---

### 4️⃣ Actions（业务逻辑层）

**作用**：处理复杂的业务逻辑，可以是异步的

```js
actions: {
  // 基本格式：actionName(context, payload)
  // context 包含：{ state, commit, dispatch, getters }
  
  // 简单action：直接提交 mutation
  increment({ commit }) {
    commit('INCREMENT')
  },
  
  // 异步action：等待API响应
  async fetchUser({ commit }, userId) {
    try {
      const response = await fetch(`/api/users/${userId}`)
      const user = await response.json()
      commit('SET_USER', user)
    } catch (error) {
      commit('SET_ERROR', error.message)
    }
  },
  
  // 复杂action：调用多个 mutation
  async login({ commit, dispatch }, credentials) {
    // 1. 设置加载状态
    commit('SET_LOADING', true)
    
    try {
      // 2. 调用登录 API
      const response = await fetch('/api/login', {
        method: 'POST',
        body: JSON.stringify(credentials)
      })
      const data = await response.json()
      
      // 3. 保存用户信息
      commit('SET_USER', data.user)
      commit('SET_TOKEN', data.token)
      
      // 4. 加载用户数据（调用另一个 action）
      await dispatch('fetchUserData')
      
      return data
    } catch (error) {
      commit('SET_ERROR', error.message)
      throw error
    } finally {
      // 5. 取消加载状态
      commit('SET_LOADING', false)
    }
  },
  
  // 条件判断
  incrementIfOdd({ state, commit }) {
    if (state.count % 2 === 1) {
      commit('INCREMENT')
    }
  }
}
```

**调用方式**：

```js
// 方式1：不带参数
store.dispatch('increment')

// 方式2：带参数
store.dispatch('fetchUser', 123)

// 方式3：对象风格
store.dispatch({
  type: 'login',
  username: 'admin',
  password: '123456'
})

// 方式4：async/await（处理返回值）
const user = await store.dispatch('login', credentials)
```

---

## 📊 第六章：完整流程图

### 数据流向

```
┌──────────────────────────────────────────────────────────────┐
│                         Vuex Store                           │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌────────────────────────────────────────────────────┐     │
│  │ State（数据仓库）                                    │     │
│  │ { count: 0, user: null }                          │     │
│  └────────────────────────────────────────────────────┘     │
│          ↑                            ↑                      │
│          │ 修改（commit）             │ 读取                 │
│          │                            │                      │
│  ┌───────┴─────────┐       ┌─────────┴──────────┐          │
│  │ Mutations       │       │ Getters            │          │
│  │ SET_USER        │       │ isLoggedIn         │          │
│  │ INCREMENT       │       │ cartTotal          │          │
│  └───────┬─────────┘       └────────────────────┘          │
│          ↑ commit                                            │
│  ┌───────┴─────────────────────────────────────────────┐   │
│  │ Actions（业务逻辑）                                   │   │
│  │ - 可以异步                                            │   │
│  │ - 可以调用多个 mutation                              │   │
│  │ - 可以包含复杂逻辑                                    │   │
│  └───────┬─────────────────────────────────────────────┘   │
│          ↑ dispatch                                          │
└──────────┼──────────────────────────────────────────────────┘
           │
    ┌──────┴──────┐
    │ Component   │
    │ (组件)      │
    └─────────────┘
```

### 用户操作完整流程

```
用户点击按钮
    ↓
组件调用 store.dispatch('login', credentials)
    ↓
Action 开始执行
    ↓
调用后端 API（异步等待）
    ↓
API 返回数据
    ↓
Action 内部调用 commit('SET_USER', user)
    ↓
Mutation 修改 State
    ↓
State 改变触发响应式更新
    ↓
所有使用该数据的组件自动重新渲染
    ↓
用户看到界面更新
```

---

## 💡 第七章：实战案例 - 购物车

### Store 定义

```js
// src/store/index.js
import { createStore } from 'vuex'

export default createStore({
  state: {
    // 购物车商品列表
    cartItems: [],
    // 所有商品
    products: [
      { id: 1, name: '苹果', price: 10, stock: 100 },
      { id: 2, name: '香蕉', price: 5, stock: 50 }
    ]
  },

  getters: {
    // 购物车总价
    cartTotal(state) {
      return state.cartItems.reduce((total, item) => {
        return total + item.price * item.quantity
      }, 0)
    },

    // 购物车商品数量
    cartCount(state) {
      return state.cartItems.reduce((count, item) => {
        return count + item.quantity
      }, 0)
    },

    // 根据ID查找商品
    getProductById: (state) => (id) => {
      return state.products.find(p => p.id === id)
    }
  },

  mutations: {
    // 添加商品到购物车
    ADD_TO_CART(state, product) {
      // 检查购物车中是否已有该商品
      const item = state.cartItems.find(i => i.id === product.id)
      
      if (item) {
        // 已存在，增加数量
        item.quantity++
      } else {
        // 不存在，添加新商品
        state.cartItems.push({
          ...product,
          quantity: 1
        })
      }
    },

    // 从购物车移除商品
    REMOVE_FROM_CART(state, productId) {
      const index = state.cartItems.findIndex(i => i.id === productId)
      if (index > -1) {
        state.cartItems.splice(index, 1)
      }
    },

    // 减少商品库存
    DECREASE_STOCK(state, productId) {
      const product = state.products.find(p => p.id === productId)
      if (product && product.stock > 0) {
        product.stock--
      }
    },

    // 清空购物车
    CLEAR_CART(state) {
      state.cartItems = []
    }
  },

  actions: {
    // 添加到购物车（包含库存检查）
    addToCart({ state, commit, getters }, productId) {
      const product = getters.getProductById(productId)
      
      if (!product) {
        alert('商品不存在')
        return
      }

      if (product.stock <= 0) {
        alert('库存不足')
        return
      }

      // 添加到购物车
      commit('ADD_TO_CART', product)
      
      // 减少库存
      commit('DECREASE_STOCK', productId)
    },

    // 结算（模拟异步API调用）
    async checkout({ state, commit }) {
      try {
        // 模拟调用支付API
        const response = await fetch('/api/checkout', {
          method: 'POST',
          body: JSON.stringify({
            items: state.cartItems
          })
        })

        if (response.ok) {
          // 清空购物车
          commit('CLEAR_CART')
          alert('结算成功！')
        }
      } catch (error) {
        alert('结算失败：' + error.message)
      }
    }
  }
})
```

### 商品列表组件

```vue
<!-- ProductList.vue -->
<template>
  <div class="product-list">
    <h2>商品列表</h2>
    <div v-for="product in products" :key="product.id" class="product-item">
      <h3>{{ product.name }}</h3>
      <p>价格: ¥{{ product.price }}</p>
      <p>库存: {{ product.stock }}</p>
      <button 
        @click="addToCart(product.id)"
        :disabled="product.stock === 0"
      >
        加入购物车
      </button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()

// 获取商品列表
const products = computed(() => store.state.products)

// 添加到购物车
const addToCart = (productId) => {
  store.dispatch('addToCart', productId)
}
</script>
```

### 购物车组件

```vue
<!-- ShoppingCart.vue -->
<template>
  <div class="shopping-cart">
    <h2>购物车 ({{ cartCount }})</h2>
    
    <div v-if="cartItems.length === 0">
      购物车是空的
    </div>
    
    <div v-else>
      <div v-for="item in cartItems" :key="item.id" class="cart-item">
        <h4>{{ item.name }}</h4>
        <p>单价: ¥{{ item.price }}</p>
        <p>数量: {{ item.quantity }}</p>
        <p>小计: ¥{{ item.price * item.quantity }}</p>
        <button @click="removeItem(item.id)">移除</button>
      </div>
      
      <div class="cart-footer">
        <h3>总价: ¥{{ cartTotal }}</h3>
        <button @click="checkout">结算</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()

// 购物车商品
const cartItems = computed(() => store.state.cartItems)

// 购物车总数
const cartCount = computed(() => store.getters.cartCount)

// 购物车总价
const cartTotal = computed(() => store.getters.cartTotal)

// 移除商品
const removeItem = (productId) => {
  store.commit('REMOVE_FROM_CART', productId)
}

// 结算
const checkout = () => {
  store.dispatch('checkout')
}
</script>
```

### Header 组件

```vue
<!-- Header.vue -->
<template>
  <header>
    <h1>我的商店</h1>
    <div class="cart-icon">
      🛒 购物车 ({{ cartCount }})
      <span v-if="cartTotal > 0">¥{{ cartTotal }}</span>
    </div>
  </header>
</template>

<script setup>
import { computed } from 'vue'
import { useStore } from 'vuex'

const store = useStore()

const cartCount = computed(() => store.getters.cartCount)
const cartTotal = computed(() => store.getters.cartTotal)
</script>
```

---

## 🎓 第八章：常见问题解答

### Q1: 什么时候该用 Vuex？

**适合用 Vuex**：
- ✅ 多个组件需要共享同一份数据
- ✅ 需要在不同路由之间保持状态
- ✅ 数据需要持久化（配合 localStorage）
- ✅ 应用较复杂，组件层级较深

**不适合用 Vuex**：
- ❌ 简单的父子组件通信（用 props/emit）
- ❌ 只在一个组件内使用的数据（用 ref/reactive）
- ❌ 临时的 UI 状态（如弹窗显示隐藏）

### Q2: State、Getter、Mutation、Action 的区别？

| 概念 | 作用 | 何时使用 | 能否异步 |
|------|------|----------|----------|
| **State** | 存数据 | 需要共享数据时 | - |
| **Getter** | 读数据、计算派生数据 | 需要计算属性时 | - |
| **Mutation** | 改数据 | 所有修改 state 的操作 | ❌ 必须同步 |
| **Action** | 业务逻辑 | 异步操作、复杂逻辑 | ✅ 可以异步 |

**记忆口诀**：
- State **存**数据
- Getter **读**数据
- Mutation **改**数据（同步）
- Action **做**事情（异步）

### Q3: 为什么要分 Mutation 和 Action？

因为 **Vuex DevTools 需要准确记录状态变化的时机**。

```js
// 如果 mutation 可以异步：
mutations: {
  async FETCH_USER(state) {
    const user = await fetch('/api/user')  // 假设允许异步
    state.user = user
  }
}

// 问题：
// 1. DevTools 不知道什么时候状态会变（异步的）
// 2. 无法准确记录状态变化的历史
// 3. 时间旅行调试会失效
```

**解决方案**：
- **Mutation**：只做同步修改，让 DevTools 能准确记录
- **Action**：处理异步，完成后再调用 mutation

### Q4: 直接修改 state 会怎么样？

```js
// ❌ 直接修改
store.state.count = 100

// 结果：
// - 数据确实会变
// - 但 DevTools 无法追踪
// - 违反了 Vuex 的设计原则
// - 团队协作时容易出问题

// ✅ 通过 mutation
store.commit('SET_COUNT', 100)

// 结果：
// - 数据正确变化
// - DevTools 完整记录
// - 代码易维护
```

### Q5: Getter 和 Computed 有什么区别?

```js
// Getter（在 store 中定义，全局共享）
getters: {
  doneTodos: state => state.todos.filter(t => t.done)
}

// Computed（在组件中定义，局部使用）
computed: {
  doneTodos() {
    return this.$store.state.todos.filter(t => t.done)
  }
}
```

**区别**：
- **Getter**：定义一次，所有组件都能用（推荐）
- **Computed**：每个组件都要定义一次（繁琐）

**什么时候用 Computed？**
- 组件特有的计算逻辑
- 不需要在其他组件中复用

### Q6: 可以有多个 Store 吗？

**不推荐！** Vuex 推荐使用 **单一状态树**（一个 store）。

如果应用很大，用 **模块（modules）** 来组织：

```js
// store/index.js
import { createStore } from 'vuex'
import user from './modules/user'
import cart from './modules/cart'

export default createStore({
  modules: {
    user,   // 用户模块
    cart    // 购物车模块
  }
})

// store/modules/user.js
export default {
  namespaced: true,  // 命名空间
  state: { ... },
  mutations: { ... },
  actions: { ... }
}

// 使用
store.state.user.name       // 访问模块的 state
store.commit('user/SET_NAME', 'Tom')  // 调用模块的 mutation
store.dispatch('user/login', credentials)  // 调用模块的 action
```

---

## 🚀 第九章：最佳实践

### 1. Mutation 命名用大写

```js
// ✅ 推荐：大写+下划线
mutations: {
  SET_USER(state, user) { ... },
  INCREMENT_COUNTER(state) { ... },
  ADD_TODO(state, todo) { ... }
}

// ❌ 不推荐：小写驼峰
mutations: {
  setUser(state, user) { ... }
}
```

**原因**：一眼就能区分 mutation 和普通函数

### 2. Action 命名用小写驼峰

```js
// ✅ 推荐
actions: {
  fetchUser({ commit }) { ... },
  login({ commit }, credentials) { ... }
}
```

### 3. 用常量管理 Mutation 类型

```js
// store/mutation-types.js
export const SET_USER = 'SET_USER'
export const INCREMENT = 'INCREMENT'

// store/index.js
import { SET_USER, INCREMENT } from './mutation-types'

export default createStore({
  mutations: {
    [SET_USER](state, user) { ... },
    [INCREMENT](state) { ... }
  }
})

// 组件中
import { SET_USER } from '@/store/mutation-types'
store.commit(SET_USER, user)
```

**优势**：
- 避免拼写错误
- IDE 自动补全
- 方便重命名

### 4. Payload 用对象，不用多个参数

```js
// ❌ 不推荐：多个参数
mutations: {
  ADD_TODO(state, id, text, done) { ... }
}
store.commit('ADD_TODO', 1, '学习Vuex', false)

// ✅ 推荐：一个对象
mutations: {
  ADD_TODO(state, { id, text, done }) { ... }
}
store.commit('ADD_TODO', { id: 1, text: '学习Vuex', done: false })
```

### 5. 组件中用 computed 包装 state

```js
// ❌ 不推荐：直接使用
const count = store.state.count  // 失去响应式！

// ✅ 推荐：用 computed
const count = computed(() => store.state.count)
```

### 6. 复杂操作用 Action，简单操作也可以用 Action

```js
// ✅ 推荐：统一用 action
actions: {
  increment({ commit }) {
    commit('INCREMENT')
  }
}

// 组件中
store.dispatch('increment')

// 优势：
// - 统一接口
// - 后续如需加逻辑，只需修改 action
// - 不需要改组件代码
```

### 7. 持久化 State

```js
// 安装插件
npm install vuex-persistedstate

// store/index.js
import createPersistedState from 'vuex-persistedstate'

export default createStore({
  // ...
  plugins: [
    createPersistedState({
      storage: window.localStorage,  // 使用 localStorage
      paths: ['user', 'token']  // 只持久化这些字段
    })
  ]
})
```

---

## 📚 第十章：学习路线图

### 阶段1：理解概念（1天）
- [ ] 理解为什么需要 Vuex
- [ ] 理解 State、Getter、Mutation、Action 的作用
- [ ] 手写一个简单的 counter 示例

### 阶段2：基础实践（2-3天）
- [ ] 实现购物车案例
- [ ] 实现待办事项（Todo List）
- [ ] 实现用户登录状态管理

### 阶段3：进阶使用（1周）
- [ ] 学习 Modules（模块化）
- [ ] 学习持久化插件
- [ ] 学习 DevTools 调试

### 阶段4：项目实战（持续）
- [ ] 在真实项目中使用 Vuex
- [ ] 优化 Store 结构
- [ ] 总结最佳实践

---

## 🎉 总结

### 一句话总结

**Vuex 就是一个"全局数据管家"，让所有组件都能方便地读取和修改共享数据。**

### 核心要点

1. **State**：数据仓库（存）
2. **Getters**：计算属性（读）
3. **Mutations**：状态修改（改，同步）
4. **Actions**：业务逻辑（做，异步）

### 记忆口诀

```
State 存数据，
Getter 来计算，
Mutation 改状态，
Action 做业务。

修改必须通过 Mutation，
异步逻辑放在 Action，
组件读取用 Computed，
全局共享用 Vuex。
```

### 下一步

- 🔗 [Vuex 官方文档](https://vuex.vuejs.org/zh/)
- 💻 动手实现一个完整的项目
- 🎯 学习 Pinia（Vue 3 推荐的新状态管理库）

---

**恭喜你完成 Vuex 学习！** 🎊

现在你已经掌握了 Vuex 的核心概念和使用方法，去写代码吧！

