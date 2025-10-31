# Computed 和 Composition API 完全指南

> 从 Vue 2 到 Vue 3，从 Options API 到 Composition API，深入理解响应式系统

---

## 📚 目录

1. [Computed 计算属性基础](#第一章computed-计算属性基础)
2. [Vue 2 Options API](#第二章vue-2-options-api)
3. [Vue 3 Composition API](#第三章vue-3-composition-api)
4. [响应式系统对比](#第四章响应式系统对比-vue-2-vs-vue-3)
5. [实战案例](#第五章实战案例)
6. [最佳实践](#第六章最佳实践)

---

## 🎯 第一章：Computed 计算属性基础

### 什么是 Computed？

**Computed（计算属性）** 是基于已有数据计算出新数据的**响应式属性**。

### 生活化类比：Excel 表格

想象你在 Excel 中：

```
| 商品  | 单价 | 数量 | 总价        |
|-------|------|------|-------------|
| 苹果  | 10   | 5    | =B2*C2      | ← 这就是 computed！
| 香蕉  | 5    | 3    | =B3*C3      |
```

- **单价、数量** = 基础数据（`data`）
- **总价** = 计算属性（`computed`）
- 当单价或数量变化时，总价**自动更新**

### 为什么需要 Computed？

#### ❌ 不用 Computed：在模板中直接计算

```vue
<template>
  <div>
    <!-- 问题1：代码重复 -->
    <p>总价: {{ price * quantity }}</p>
    <p>含税总价: {{ price * quantity * 1.1 }}</p>
    <p>折扣价: {{ price * quantity * 0.8 }}</p>
    
    <!-- 问题2：逻辑复杂，难以维护 -->
    <p>状态: {{ 
      stock > 100 ? '库存充足' : 
      stock > 10 ? '库存紧张' : 
      stock > 0 ? '即将售罄' : '已售罄' 
    }}</p>
    
    <!-- 问题3：每次渲染都会重新计算 -->
    <p>随机数: {{ Math.random() }}</p>
  </div>
</template>
```

#### ✅ 用 Computed：优雅、高效

```vue
<template>
  <div>
    <p>总价: {{ total }}</p>
    <p>含税总价: {{ totalWithTax }}</p>
    <p>折扣价: {{ discountedTotal }}</p>
    <p>状态: {{ stockStatus }}</p>
  </div>
</template>

<script>
export default {
  data() {
    return {
      price: 10,
      quantity: 5,
      stock: 50
    }
  },
  computed: {
    // 简洁清晰
    total() {
      return this.price * this.quantity
    },
    
    totalWithTax() {
      return this.total * 1.1
    },
    
    discountedTotal() {
      return this.total * 0.8
    },
    
    stockStatus() {
      if (this.stock > 100) return '库存充足'
      if (this.stock > 10) return '库存紧张'
      if (this.stock > 0) return '即将售罄'
      return '已售罄'
    }
  }
}
</script>
```

### Computed 的三大特性

#### 1️⃣ **响应式**（自动更新）

```js
data() {
  return {
    price: 10,
    quantity: 5
  }
},
computed: {
  total() {
    return this.price * this.quantity  // 50
  }
}

// 当 price 或 quantity 变化时，total 自动更新！
this.price = 20  // total 变成 100
this.quantity = 3  // total 变成 60
```

#### 2️⃣ **缓存**（性能优化）

```js
computed: {
  expensiveComputation() {
    console.log('计算中...')
    let result = 0
    for (let i = 0; i < 1000000; i++) {
      result += i
    }
    return result
  }
}

// 第一次访问：执行计算，输出"计算中..."
this.expensiveComputation  // 499999500000

// 第二次访问：直接返回缓存，不输出
this.expensiveComputation  // 499999500000（立即返回）

// 只有依赖的数据变化时，才会重新计算
```

#### 3️⃣ **只读**（默认情况下）

```js
computed: {
  fullName() {
    return this.firstName + ' ' + this.lastName
  }
}

// ❌ 不能直接赋值
this.fullName = 'John Doe'  // 警告：computed 是只读的！

// ✅ 要改变 computed，需要改变其依赖的数据
this.firstName = 'John'
this.lastName = 'Doe'
// 此时 fullName 自动变成 'John Doe'
```

### Computed vs Methods 对比

```vue
<script>
export default {
  data() {
    return {
      count: 1
    }
  },
  
  // Computed：有缓存
  computed: {
    doubleCount() {
      console.log('computed 执行')
      return this.count * 2
    }
  },
  
  // Methods：无缓存
  methods: {
    getDoubleCount() {
      console.log('method 执行')
      return this.count * 2
    }
  }
}
</script>

<template>
  <div>
    <!-- 多次访问 computed，只执行一次 -->
    <p>{{ doubleCount }}</p>  <!-- 输出：computed 执行，2 -->
    <p>{{ doubleCount }}</p>  <!-- 不输出，直接返回缓存的 2 -->
    <p>{{ doubleCount }}</p>  <!-- 不输出，直接返回缓存的 2 -->
    
    <!-- 多次调用 method，每次都执行 -->
    <p>{{ getDoubleCount() }}</p>  <!-- 输出：method 执行，2 -->
    <p>{{ getDoubleCount() }}</p>  <!-- 输出：method 执行，2 -->
    <p>{{ getDoubleCount() }}</p>  <!-- 输出：method 执行，2 -->
  </div>
</template>
```

**对比总结**：

| 特性 | Computed | Methods |
|------|----------|---------|
| **缓存** | ✅ 有缓存，依赖不变不重新计算 | ❌ 无缓存，每次调用都执行 |
| **响应式** | ✅ 依赖变化自动更新 | ❌ 需要手动调用 |
| **使用场景** | 计算属性、派生数据 | 事件处理、主动调用 |
| **性能** | 🚀 高（有缓存） | ⚠️ 低（无缓存） |
| **调用方式** | `{{ computed }}` | `{{ method() }}` |

**何时用 Computed？何时用 Methods？**

```js
// ✅ 用 Computed：需要根据现有数据计算新值
computed: {
  fullName() { return this.firstName + ' ' + this.lastName },
  filteredList() { return this.list.filter(item => item.active) },
  total() { return this.items.reduce((sum, item) => sum + item.price, 0) }
}

// ✅ 用 Methods：处理事件、执行操作
methods: {
  handleClick() { ... },
  submitForm() { ... },
  fetchData() { ... }
}
```

---

## 📦 第二章：Vue 2 Options API

### Options API 是什么？

Vue 2 使用 **Options API**（选项式 API），将组件的**不同功能**分别放在**不同的选项**中。

```vue
<script>
export default {
  // 组件名
  name: 'MyComponent',
  
  // 接收的属性
  props: ['title'],
  
  // 本地数据
  data() {
    return {
      count: 0,
      message: 'Hello'
    }
  },
  
  // 计算属性
  computed: {
    doubleCount() {
      return this.count * 2
    }
  },
  
  // 方法
  methods: {
    increment() {
      this.count++
    }
  },
  
  // 监听器
  watch: {
    count(newVal, oldVal) {
      console.log(`count 从 ${oldVal} 变成 ${newVal}`)
    }
  },
  
  // 生命周期钩子
  created() {
    console.log('组件创建完成')
  },
  
  mounted() {
    console.log('组件挂载完成')
  }
}
</script>
```

### Vue 2 的响应式原理：Object.defineProperty

Vue 2 使用 **`Object.defineProperty`** 实现响应式。

#### 原理演示

```js
// Vue 2 底层做了什么？
const data = {
  count: 0
}

// 使用 Object.defineProperty 拦截访问和修改
let internalValue = data.count

Object.defineProperty(data, 'count', {
  // 读取时
  get() {
    console.log('读取 count:', internalValue)
    return internalValue
  },
  
  // 修改时
  set(newValue) {
    console.log('修改 count:', internalValue, '->', newValue)
    internalValue = newValue
    
    // 通知视图更新
    updateView()
  }
})

// 测试
data.count  // 输出：读取 count: 0
data.count = 10  // 输出：修改 count: 0 -> 10
```

#### Vue 2 响应式的限制

```js
export default {
  data() {
    return {
      user: {
        name: 'Tom',
        age: 18
      },
      list: [1, 2, 3]
    }
  },
  
  methods: {
    test() {
      // ✅ 可以响应：修改已存在的属性
      this.user.name = 'Jerry'
      
      // ❌ 不能响应：添加新属性
      this.user.email = 'tom@example.com'  // ❌ 不会触发更新！
      
      // ✅ 解决方案：使用 Vue.set
      this.$set(this.user, 'email', 'tom@example.com')
      
      // ❌ 不能响应：直接修改数组索引
      this.list[0] = 100  // ❌ 不会触发更新！
      
      // ✅ 解决方案1：使用 Vue.set
      this.$set(this.list, 0, 100)
      
      // ✅ 解决方案2：使用数组方法
      this.list.splice(0, 1, 100)
    }
  }
}
```

**Vue 2 响应式的坑**：

```js
// ❌ 这些操作不会触发更新
data.newProperty = 'value'  // 添加新属性
delete data.property  // 删除属性
array[index] = value  // 修改数组元素
array.length = 0  // 修改数组长度

// ✅ 必须使用特殊 API
Vue.set(data, 'newProperty', 'value')
Vue.delete(data, 'property')
this.$set(this.array, index, value)
this.array.splice(0, this.array.length)
```

### Vue 2 完整示例

```vue
<template>
  <div class="counter">
    <h2>计数器: {{ count }}</h2>
    <p>双倍: {{ doubleCount }}</p>
    <p>状态: {{ status }}</p>
    
    <button @click="increment">+1</button>
    <button @click="decrement">-1</button>
    <button @click="reset">重置</button>
    
    <input v-model="firstName" placeholder="名">
    <input v-model="lastName" placeholder="姓">
    <p>全名: {{ fullName }}</p>
  </div>
</template>

<script>
export default {
  name: 'Counter',
  
  // 数据
  data() {
    return {
      count: 0,
      firstName: '',
      lastName: ''
    }
  },
  
  // 计算属性
  computed: {
    // 简单计算
    doubleCount() {
      return this.count * 2
    },
    
    // 条件判断
    status() {
      if (this.count > 10) return '很高'
      if (this.count > 0) return '正常'
      if (this.count === 0) return '归零'
      return '负数'
    },
    
    // 拼接字符串
    fullName() {
      return this.firstName + ' ' + this.lastName
    }
  },
  
  // 方法
  methods: {
    increment() {
      this.count++
    },
    
    decrement() {
      this.count--
    },
    
    reset() {
      this.count = 0
    }
  },
  
  // 监听器
  watch: {
    count(newVal, oldVal) {
      console.log(`计数从 ${oldVal} 变成 ${newVal}`)
      
      if (newVal > 100) {
        alert('计数太高了！')
        this.count = 100
      }
    }
  },
  
  // 生命周期
  created() {
    console.log('组件创建')
  },
  
  mounted() {
    console.log('组件挂载')
  }
}
</script>
```

---

## 🚀 第三章：Vue 3 Composition API

### Composition API 是什么？

Vue 3 引入了 **Composition API**（组合式 API），允许你用**函数**的方式组织代码。

### 为什么需要 Composition API？

#### Options API 的问题

```vue
<script>
// Vue 2 Options API
export default {
  data() {
    return {
      // 🔴 用户相关数据
      userName: '',
      userAge: 0,
      
      // 🔵 购物车相关数据
      cartItems: [],
      cartTotal: 0,
      
      // 🟢 搜索相关数据
      searchQuery: '',
      searchResults: []
    }
  },
  
  computed: {
    // 🔴 用户相关计算
    isAdult() { return this.userAge >= 18 },
    
    // 🔵 购物车相关计算
    cartCount() { return this.cartItems.length },
    
    // 🟢 搜索相关计算
    hasResults() { return this.searchResults.length > 0 }
  },
  
  methods: {
    // 🔴 用户相关方法
    updateUserName() { ... },
    
    // 🔵 购物车相关方法
    addToCart() { ... },
    
    // 🟢 搜索相关方法
    search() { ... }
  }
}

// 问题：
// 1. 相同功能的代码被分散在不同选项中
// 2. 组件大了之后，难以维护
// 3. 逻辑复用困难（需要 mixin，但 mixin 有命名冲突问题）
</script>
```

#### Composition API 的优势

```vue
<script setup>
import { ref, computed } from 'vue'

// ✅ 把相关的代码组织在一起

// 🔴 用户相关逻辑（集中在一起）
const userName = ref('')
const userAge = ref(0)
const isAdult = computed(() => userAge.value >= 18)
const updateUserName = () => { ... }

// 🔵 购物车相关逻辑（集中在一起）
const cartItems = ref([])
const cartTotal = ref(0)
const cartCount = computed(() => cartItems.value.length)
const addToCart = () => { ... }

// 🟢 搜索相关逻辑（集中在一起）
const searchQuery = ref('')
const searchResults = ref([])
const hasResults = computed(() => searchResults.value.length > 0)
const search = () => { ... }
</script>
```

**甚至可以提取到单独的函数**：

```js
// composables/useUser.js
export function useUser() {
  const userName = ref('')
  const userAge = ref(0)
  const isAdult = computed(() => userAge.value >= 18)
  const updateUserName = () => { ... }
  
  return {
    userName,
    userAge,
    isAdult,
    updateUserName
  }
}

// 在组件中使用
<script setup>
import { useUser } from '@/composables/useUser'

const { userName, userAge, isAdult, updateUserName } = useUser()
</script>
```

### Vue 3 响应式 API

#### 1. ref（基本类型响应式）

```js
import { ref } from 'vue'

// 创建响应式数据
const count = ref(0)
const message = ref('Hello')
const isActive = ref(true)

console.log(count)  // { value: 0 }（是一个对象！）
console.log(count.value)  // 0（要通过 .value 访问）

// 修改值
count.value = 10
message.value = 'World'
isActive.value = false
```

**为什么需要 `.value`？**

```js
// JavaScript 的基本类型（数字、字符串、布尔）是值传递，无法追踪变化
let count = 0
count = 10  // Vue 无法知道这个变化

// Vue 3 用一个对象包装，通过 getter/setter 追踪变化
const count = ref(0)
count.value = 10  // Vue 可以追踪到！
```

**在模板中自动解包**：

```vue
<script setup>
import { ref } from 'vue'

const count = ref(0)

// 在 JS 中需要 .value
console.log(count.value)

// 在模板中自动解包，不需要 .value
</script>

<template>
  <div>{{ count }}</div>  <!-- ✅ 直接用 count，不用 count.value -->
  <button @click="count++">+1</button>  <!-- ✅ 自动解包 -->
</template>
```

#### 2. reactive（对象响应式）

```js
import { reactive } from 'vue'

// 创建响应式对象
const user = reactive({
  name: 'Tom',
  age: 18,
  hobbies: ['reading', 'coding']
})

// 直接访问和修改（不需要 .value）
console.log(user.name)  // Tom
user.name = 'Jerry'
user.age++
user.hobbies.push('gaming')

// ✅ 可以添加新属性（Vue 2 不行！）
user.email = 'tom@example.com'  // ✅ 可以响应！

// ✅ 可以直接修改数组索引（Vue 2 不行！）
user.hobbies[0] = 'swimming'  // ✅ 可以响应！
```

#### 3. computed（计算属性）

```js
import { ref, computed } from 'vue'

const firstName = ref('Tom')
const lastName = ref('Cat')

// 只读 computed
const fullName = computed(() => {
  return firstName.value + ' ' + lastName.value
})

console.log(fullName.value)  // Tom Cat（需要 .value）

// ❌ computed 默认只读
fullName.value = 'Jerry Mouse'  // 警告！

// ✅ 可写 computed
const fullName = computed({
  // getter
  get() {
    return firstName.value + ' ' + lastName.value
  },
  // setter
  set(newValue) {
    const parts = newValue.split(' ')
    firstName.value = parts[0]
    lastName.value = parts[1]
  }
})

fullName.value = 'Jerry Mouse'  // ✅ 可以赋值
console.log(firstName.value)  // Jerry
console.log(lastName.value)  // Mouse
```

### Vue 3 完整示例

```vue
<template>
  <div class="counter">
    <h2>计数器: {{ count }}</h2>
    <p>双倍: {{ doubleCount }}</p>
    <p>状态: {{ status }}</p>
    
    <button @click="increment">+1</button>
    <button @click="decrement">-1</button>
    <button @click="reset">重置</button>
    
    <input v-model="user.firstName" placeholder="名">
    <input v-model="user.lastName" placeholder="姓">
    <p>全名: {{ fullName }}</p>
  </div>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'

// 基本类型用 ref
const count = ref(0)

// 对象用 reactive
const user = reactive({
  firstName: '',
  lastName: ''
})

// 计算属性
const doubleCount = computed(() => count.value * 2)

const status = computed(() => {
  if (count.value > 10) return '很高'
  if (count.value > 0) return '正常'
  if (count.value === 0) return '归零'
  return '负数'
})

const fullName = computed(() => {
  return user.firstName + ' ' + user.lastName
})

// 方法
const increment = () => {
  count.value++
}

const decrement = () => {
  count.value--
}

const reset = () => {
  count.value = 0
}

// 监听器
watch(count, (newVal, oldVal) => {
  console.log(`计数从 ${oldVal} 变成 ${newVal}`)
  
  if (newVal > 100) {
    alert('计数太高了！')
    count.value = 100
  }
})

// 生命周期
import { onMounted } from 'vue'

onMounted(() => {
  console.log('组件挂载完成')
})
</script>
```

### `<script setup>` 语法糖

```vue
<!-- ❌ 不用 setup 语法糖（繁琐） -->
<script>
import { ref, computed } from 'vue'

export default {
  setup() {
    const count = ref(0)
    const doubleCount = computed(() => count.value * 2)
    const increment = () => count.value++
    
    // 必须 return 才能在模板中使用
    return {
      count,
      doubleCount,
      increment
    }
  }
}
</script>

<!-- ✅ 用 setup 语法糖（简洁） -->
<script setup>
import { ref, computed } from 'vue'

// 不需要 return，自动可用
const count = ref(0)
const doubleCount = computed(() => count.value * 2)
const increment = () => count.value++
</script>
```

---

## ⚔️ 第四章：响应式系统对比 Vue 2 vs Vue 3

### 核心原理对比

| 特性 | Vue 2 | Vue 3 |
|------|-------|-------|
| **实现原理** | `Object.defineProperty` | `Proxy` |
| **浏览器支持** | IE 9+ | 现代浏览器（不支持 IE） |
| **响应式能力** | 有限制 | 完全响应式 |
| **性能** | 较慢 | 更快 |

### 1. 添加新属性

```js
// Vue 2
export default {
  data() {
    return {
      user: { name: 'Tom' }
    }
  },
  methods: {
    addEmail() {
      // ❌ 不响应
      this.user.email = 'tom@example.com'
      
      // ✅ 需要用 Vue.set
      this.$set(this.user, 'email', 'tom@example.com')
    }
  }
}

// Vue 3
<script setup>
import { reactive } from 'vue'

const user = reactive({ name: 'Tom' })

const addEmail = () => {
  // ✅ 直接添加，自动响应
  user.email = 'tom@example.com'
}
</script>
```

### 2. 删除属性

```js
// Vue 2
methods: {
  removeEmail() {
    // ❌ 不响应
    delete this.user.email
    
    // ✅ 需要用 Vue.delete
    this.$delete(this.user, 'email')
  }
}

// Vue 3
const removeEmail = () => {
  // ✅ 直接删除，自动响应
  delete user.email
}
```

### 3. 数组操作

```js
// Vue 2
data() {
  return {
    list: [1, 2, 3]
  }
},
methods: {
  updateArray() {
    // ❌ 不响应：直接修改索引
    this.list[0] = 100
    
    // ❌ 不响应：修改长度
    this.list.length = 0
    
    // ✅ 响应：使用数组方法
    this.list.push(4)
    this.list.splice(0, 1, 100)
    
    // ✅ 响应：使用 Vue.set
    this.$set(this.list, 0, 100)
  }
}

// Vue 3
const list = reactive([1, 2, 3])

const updateArray = () => {
  // ✅ 全部响应！
  list[0] = 100  // ✅
  list.length = 0  // ✅
  list.push(4)  // ✅
}
```

### 4. 监听深层对象

```js
// Vue 2
data() {
  return {
    user: {
      profile: {
        address: {
          city: 'Beijing'
        }
      }
    }
  }
},
watch: {
  // ❌ 浅层监听，深层变化监听不到
  user(newVal) {
    console.log('user 变化')
  },
  
  // ✅ 深层监听（性能开销大）
  user: {
    handler(newVal) {
      console.log('user 变化')
    },
    deep: true
  }
}

// Vue 3（Proxy 原生支持深层监听）
import { reactive, watch } from 'vue'

const user = reactive({
  profile: {
    address: {
      city: 'Beijing'
    }
  }
})

// ✅ 自动深层响应
watch(user, (newVal) => {
  console.log('user 变化')
})

// 修改深层属性会自动触发
user.profile.address.city = 'Shanghai'  // ✅ 自动监听到
```

### 5. 性能对比

```js
// Vue 2：需要递归遍历所有属性
const data = {
  a: 1,
  b: 2,
  c: {
    d: 3,
    e: {
      f: 4
    }
  }
}

// Vue 2 初始化时：
// - 遍历 a, b, c
// - 遍历 c.d, c.e
// - 遍历 c.e.f
// 总共调用 Object.defineProperty 6 次

// Vue 3：懒响应式
const data = reactive({
  a: 1,
  b: 2,
  c: {
    d: 3,
    e: {
      f: 4
    }
  }
})

// Vue 3 初始化时：
// - 只创建最外层的 Proxy
// - 只有访问 c 时，才创建 c 的 Proxy
// - 只有访问 c.e 时，才创建 e 的 Proxy
// 性能更好！
```

### 完整对比表

| 操作 | Vue 2 Options API | Vue 3 Composition API |
|------|-------------------|----------------------|
| **定义数据** | `data() { return { count: 0 } }` | `const count = ref(0)` |
| **访问数据** | `this.count` | `count.value`（模板中不需要） |
| **计算属性** | `computed: { double() { ... } }` | `const double = computed(() => ...)` |
| **方法** | `methods: { increment() { ... } }` | `const increment = () => { ... }` |
| **监听器** | `watch: { count(n, o) { ... } }` | `watch(count, (n, o) => { ... })` |
| **生命周期** | `mounted() { ... }` | `onMounted(() => { ... })` |
| **添加属性** | `this.$set(obj, key, val)` | `obj.key = val` ✅ |
| **删除属性** | `this.$delete(obj, key)` | `delete obj.key` ✅ |
| **数组索引** | `this.$set(arr, idx, val)` | `arr[idx] = val` ✅ |
| **代码组织** | 按选项分散 | 按功能集中 |
| **逻辑复用** | Mixin（有问题） | Composable（优雅） |

---

## 💼 第五章：实战案例

### 案例1：待办事项（TodoList）

#### Vue 2 版本

```vue
<template>
  <div class="todo-app">
    <h1>待办事项</h1>
    
    <input 
      v-model="newTodo" 
      @keyup.enter="addTodo"
      placeholder="添加待办..."
    >
    <button @click="addTodo">添加</button>
    
    <div class="filters">
      <button @click="filter = 'all'">全部 ({{ allCount }})</button>
      <button @click="filter = 'active'">未完成 ({{ activeCount }})</button>
      <button @click="filter = 'completed'">已完成 ({{ completedCount }})</button>
    </div>
    
    <ul>
      <li v-for="todo in filteredTodos" :key="todo.id">
        <input 
          type="checkbox" 
          v-model="todo.done"
        >
        <span :class="{ done: todo.done }">{{ todo.text }}</span>
        <button @click="removeTodo(todo.id)">删除</button>
      </li>
    </ul>
    
    <p>完成度: {{ completionRate }}%</p>
  </div>
</template>

<script>
export default {
  data() {
    return {
      newTodo: '',
      filter: 'all',
      todos: []
    }
  },
  
  computed: {
    // 过滤后的列表
    filteredTodos() {
      if (this.filter === 'active') {
        return this.todos.filter(t => !t.done)
      }
      if (this.filter === 'completed') {
        return this.todos.filter(t => t.done)
      }
      return this.todos
    },
    
    // 统计数量
    allCount() {
      return this.todos.length
    },
    
    activeCount() {
      return this.todos.filter(t => !t.done).length
    },
    
    completedCount() {
      return this.todos.filter(t => t.done).length
    },
    
    // 完成率
    completionRate() {
      if (this.todos.length === 0) return 0
      return Math.round(
        (this.completedCount / this.allCount) * 100
      )
    }
  },
  
  methods: {
    addTodo() {
      if (this.newTodo.trim() === '') return
      
      this.todos.push({
        id: Date.now(),
        text: this.newTodo,
        done: false
      })
      
      this.newTodo = ''
    },
    
    removeTodo(id) {
      const index = this.todos.findIndex(t => t.id === id)
      if (index > -1) {
        this.todos.splice(index, 1)
      }
    }
  }
}
</script>

<style scoped>
.done {
  text-decoration: line-through;
  color: #999;
}
</style>
```

#### Vue 3 版本

```vue
<template>
  <div class="todo-app">
    <h1>待办事项</h1>
    
    <input 
      v-model="newTodo" 
      @keyup.enter="addTodo"
      placeholder="添加待办..."
    >
    <button @click="addTodo">添加</button>
    
    <div class="filters">
      <button @click="filter = 'all'">全部 ({{ allCount }})</button>
      <button @click="filter = 'active'">未完成 ({{ activeCount }})</button>
      <button @click="filter = 'completed'">已完成 ({{ completedCount }})</button>
    </div>
    
    <ul>
      <li v-for="todo in filteredTodos" :key="todo.id">
        <input type="checkbox" v-model="todo.done">
        <span :class="{ done: todo.done }">{{ todo.text }}</span>
        <button @click="removeTodo(todo.id)">删除</button>
      </li>
    </ul>
    
    <p>完成度: {{ completionRate }}%</p>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// 数据
const newTodo = ref('')
const filter = ref('all')
const todos = ref([])

// 计算属性
const filteredTodos = computed(() => {
  if (filter.value === 'active') {
    return todos.value.filter(t => !t.done)
  }
  if (filter.value === 'completed') {
    return todos.value.filter(t => t.done)
  }
  return todos.value
})

const allCount = computed(() => todos.value.length)

const activeCount = computed(() => {
  return todos.value.filter(t => !t.done).length
})

const completedCount = computed(() => {
  return todos.value.filter(t => t.done).length
})

const completionRate = computed(() => {
  if (allCount.value === 0) return 0
  return Math.round((completedCount.value / allCount.value) * 100)
})

// 方法
const addTodo = () => {
  if (newTodo.value.trim() === '') return
  
  todos.value.push({
    id: Date.now(),
    text: newTodo.value,
    done: false
  })
  
  newTodo.value = ''
}

const removeTodo = (id) => {
  const index = todos.value.findIndex(t => t.id === id)
  if (index > -1) {
    todos.value.splice(index, 1)
  }
}
</script>

<style scoped>
.done {
  text-decoration: line-through;
  color: #999;
}
</style>
```

### 案例2：购物车

```vue
<template>
  <div class="shopping-cart">
    <h2>购物车</h2>
    
    <!-- 商品列表 -->
    <div v-for="item in cartItems" :key="item.id" class="item">
      <h3>{{ item.name }}</h3>
      <p>单价: ¥{{ item.price }}</p>
      
      <div class="quantity">
        <button @click="decreaseQuantity(item)">-</button>
        <span>{{ item.quantity }}</span>
        <button @click="increaseQuantity(item)">+</button>
      </div>
      
      <p>小计: ¥{{ itemTotal(item) }}</p>
      <button @click="removeItem(item.id)">删除</button>
    </div>
    
    <!-- 统计 -->
    <div class="summary">
      <p>商品数量: {{ totalQuantity }}</p>
      <p>原价: ¥{{ originalTotal }}</p>
      <p v-if="hasDiscount">折扣: -¥{{ discountAmount }}</p>
      <h3>应付: ¥{{ finalTotal }}</h3>
      <button @click="checkout" :disabled="cartItems.length === 0">
        结算
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

// 购物车商品
const cartItems = ref([
  { id: 1, name: '苹果', price: 10, quantity: 2 },
  { id: 2, name: '香蕉', price: 5, quantity: 3 }
])

// 计算单个商品小计
const itemTotal = (item) => {
  return item.price * item.quantity
}

// 计算总数量
const totalQuantity = computed(() => {
  return cartItems.value.reduce((sum, item) => {
    return sum + item.quantity
  }, 0)
})

// 计算原价总计
const originalTotal = computed(() => {
  return cartItems.value.reduce((sum, item) => {
    return sum + item.price * item.quantity
  }, 0)
})

// 是否有折扣（满100减20）
const hasDiscount = computed(() => {
  return originalTotal.value >= 100
})

// 折扣金额
const discountAmount = computed(() => {
  return hasDiscount.value ? 20 : 0
})

// 最终价格
const finalTotal = computed(() => {
  return originalTotal.value - discountAmount.value
})

// 增加数量
const increaseQuantity = (item) => {
  item.quantity++
}

// 减少数量
const decreaseQuantity = (item) => {
  if (item.quantity > 1) {
    item.quantity--
  }
}

// 删除商品
const removeItem = (id) => {
  const index = cartItems.value.findIndex(item => item.id === id)
  if (index > -1) {
    cartItems.value.splice(index, 1)
  }
}

// 结算
const checkout = () => {
  alert(`结算成功！共 ¥${finalTotal.value}`)
  cartItems.value = []
}
</script>
```

### 案例3：表单验证

```vue
<template>
  <div class="form">
    <h2>用户注册</h2>
    
    <div class="field">
      <label>用户名</label>
      <input v-model="form.username" @blur="validateUsername">
      <span class="error" v-if="errors.username">{{ errors.username }}</span>
      <span class="success" v-if="!errors.username && form.username">✓</span>
    </div>
    
    <div class="field">
      <label>邮箱</label>
      <input v-model="form.email" @blur="validateEmail">
      <span class="error" v-if="errors.email">{{ errors.email }}</span>
      <span class="success" v-if="!errors.email && form.email">✓</span>
    </div>
    
    <div class="field">
      <label>密码</label>
      <input type="password" v-model="form.password" @blur="validatePassword">
      <span class="error" v-if="errors.password">{{ errors.password }}</span>
      <div class="password-strength">
        强度: <span :class="passwordStrengthClass">{{ passwordStrength }}</span>
      </div>
    </div>
    
    <div class="field">
      <label>确认密码</label>
      <input type="password" v-model="form.confirmPassword" @blur="validateConfirmPassword">
      <span class="error" v-if="errors.confirmPassword">{{ errors.confirmPassword }}</span>
    </div>
    
    <button @click="submit" :disabled="!isFormValid">
      注册
    </button>
    
    <p>表单完成度: {{ formCompleteness }}%</p>
  </div>
</template>

<script setup>
import { reactive, computed } from 'vue'

// 表单数据
const form = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 错误信息
const errors = reactive({
  username: '',
  email: '',
  password: '',
  confirmPassword: ''
})

// 验证用户名
const validateUsername = () => {
  if (form.username.length === 0) {
    errors.username = '用户名不能为空'
  } else if (form.username.length < 3) {
    errors.username = '用户名至少3个字符'
  } else if (form.username.length > 20) {
    errors.username = '用户名最多20个字符'
  } else {
    errors.username = ''
  }
}

// 验证邮箱
const validateEmail = () => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  
  if (form.email.length === 0) {
    errors.email = '邮箱不能为空'
  } else if (!emailRegex.test(form.email)) {
    errors.email = '邮箱格式不正确'
  } else {
    errors.email = ''
  }
}

// 验证密码
const validatePassword = () => {
  if (form.password.length === 0) {
    errors.password = '密码不能为空'
  } else if (form.password.length < 6) {
    errors.password = '密码至少6个字符'
  } else {
    errors.password = ''
  }
}

// 验证确认密码
const validateConfirmPassword = () => {
  if (form.confirmPassword !== form.password) {
    errors.confirmPassword = '两次密码不一致'
  } else {
    errors.confirmPassword = ''
  }
}

// 计算密码强度
const passwordStrength = computed(() => {
  const pwd = form.password
  if (pwd.length === 0) return '无'
  if (pwd.length < 6) return '弱'
  
  let strength = 0
  if (pwd.length >= 8) strength++
  if (/[a-z]/.test(pwd)) strength++
  if (/[A-Z]/.test(pwd)) strength++
  if (/[0-9]/.test(pwd)) strength++
  if (/[^a-zA-Z0-9]/.test(pwd)) strength++
  
  if (strength <= 2) return '中'
  if (strength <= 4) return '强'
  return '极强'
})

// 密码强度样式
const passwordStrengthClass = computed(() => {
  const strength = passwordStrength.value
  if (strength === '弱') return 'weak'
  if (strength === '中') return 'medium'
  if (strength === '强' || strength === '极强') return 'strong'
  return ''
})

// 表单是否有效
const isFormValid = computed(() => {
  return !errors.username && 
         !errors.email && 
         !errors.password && 
         !errors.confirmPassword &&
         form.username &&
         form.email &&
         form.password &&
         form.confirmPassword
})

// 表单完成度
const formCompleteness = computed(() => {
  let filled = 0
  if (form.username) filled++
  if (form.email) filled++
  if (form.password) filled++
  if (form.confirmPassword) filled++
  
  return Math.round((filled / 4) * 100)
})

// 提交表单
const submit = () => {
  // 全部验证一遍
  validateUsername()
  validateEmail()
  validatePassword()
  validateConfirmPassword()
  
  if (isFormValid.value) {
    alert('注册成功！')
  }
}
</script>

<style scoped>
.error {
  color: red;
  font-size: 12px;
}

.success {
  color: green;
  font-size: 12px;
}

.password-strength .weak {
  color: red;
}

.password-strength .medium {
  color: orange;
}

.password-strength .strong {
  color: green;
}
</style>
```

---

## 🎓 第六章：最佳实践

### 1. 何时用 ref，何时用 reactive？

```js
// ✅ 基本类型用 ref
const count = ref(0)
const message = ref('Hello')
const isActive = ref(true)

// ✅ 对象用 reactive
const user = reactive({
  name: 'Tom',
  age: 18
})

// ⚠️ 也可以用 ref 包装对象
const user = ref({
  name: 'Tom',
  age: 18
})
// 访问：user.value.name
// 但 reactive 更简洁：user.name

// ❌ 不推荐：reactive 包装基本类型
const count = reactive({ value: 0 })  // 繁琐！
```

**推荐规则**：
- 基本类型（数字、字符串、布尔）→ `ref`
- 对象、数组 → `reactive`

### 2. 避免 computed 中的副作用

```js
// ❌ 错误：computed 中修改数据
const doubleCount = computed(() => {
  count.value++  // ❌ 不要修改数据！
  return count.value * 2
})

// ❌ 错误：computed 中调用 API
const userData = computed(() => {
  fetch('/api/user')  // ❌ 不要异步操作！
  return ...
})

// ✅ 正确：computed 只做计算
const doubleCount = computed(() => {
  return count.value * 2
})
```

**规则**：Computed 应该是**纯函数**（无副作用）

### 3. 合理使用 watch

```js
// ✅ 用 watch：响应数据变化，执行副作用
watch(searchQuery, async (newQuery) => {
  // 搜索（异步操作）
  const results = await fetch(`/api/search?q=${newQuery}`)
  searchResults.value = results
})

// ❌ 不要用 watch 做计算
watch(count, (newCount) => {
  doubleCount.value = newCount * 2  // ❌ 应该用 computed
})

// ✅ 应该用 computed
const doubleCount = computed(() => count.value * 2)
```

**规则**：
- **Computed**：同步计算，有缓存
- **Watch**：异步操作，有副作用

### 4. 解构 reactive 会失去响应式

```js
const user = reactive({
  name: 'Tom',
  age: 18
})

// ❌ 错误：解构后失去响应式
const { name, age } = user
console.log(name)  // Tom
user.name = 'Jerry'
console.log(name)  // 还是 Tom（没变！）

// ✅ 解决方案1：使用 toRefs
import { toRefs } from 'vue'

const { name, age } = toRefs(user)
console.log(name.value)  // Tom
user.name = 'Jerry'
console.log(name.value)  // Jerry（变了！）

// ✅ 解决方案2：不解构，直接用
console.log(user.name)  // Tom
user.name = 'Jerry'
console.log(user.name)  // Jerry
```

### 5. 组合式函数（Composables）

```js
// composables/useCounter.js
import { ref, computed } from 'vue'

export function useCounter(initialValue = 0) {
  const count = ref(initialValue)
  
  const doubleCount = computed(() => count.value * 2)
  
  const increment = () => count.value++
  const decrement = () => count.value--
  const reset = () => count.value = initialValue
  
  return {
    count,
    doubleCount,
    increment,
    decrement,
    reset
  }
}

// 在组件中使用
<script setup>
import { useCounter } from '@/composables/useCounter'

const { count, doubleCount, increment, decrement, reset } = useCounter(10)
</script>

<template>
  <div>
    <p>计数: {{ count }}</p>
    <p>双倍: {{ doubleCount }}</p>
    <button @click="increment">+1</button>
    <button @click="decrement">-1</button>
    <button @click="reset">重置</button>
  </div>
</template>
```

**优势**：
- ✅ 逻辑复用
- ✅ 代码组织清晰
- ✅ 类型推导友好

### 6. Computed vs Watch 使用场景

```js
// ✅ 用 Computed：一个值依赖另一个值
const fullName = computed(() => {
  return firstName.value + ' ' + lastName.value
})

// ✅ 用 Watch：需要执行异步操作或复杂副作用
watch(searchQuery, async (newQuery) => {
  isLoading.value = true
  
  try {
    const results = await fetch(`/api/search?q=${newQuery}`)
    searchResults.value = await results.json()
  } catch (error) {
    console.error(error)
  } finally {
    isLoading.value = false
  }
})

// ✅ 用 Watch：需要在数据变化时执行多个操作
watch(userId, async (newId) => {
  // 1. 保存到 localStorage
  localStorage.setItem('userId', newId)
  
  // 2. 上报分析
  analytics.track('user_changed', { userId: newId })
  
  // 3. 加载用户数据
  const user = await fetchUser(newId)
  currentUser.value = user
})
```

### 7. 避免在模板中使用复杂表达式

```vue
<!-- ❌ 不推荐：模板中的复杂逻辑 -->
<template>
  <div>
    <p>{{ user.firstName + ' ' + user.lastName + (user.isVip ? ' (VIP)' : '') }}</p>
    <p>{{ items.filter(i => i.price > 100).reduce((sum, i) => sum + i.price, 0) }}</p>
  </div>
</template>

<!-- ✅ 推荐：用 computed -->
<template>
  <div>
    <p>{{ displayName }}</p>
    <p>{{ expensiveTotal }}</p>
  </div>
</template>

<script setup>
const displayName = computed(() => {
  const fullName = user.firstName + ' ' + user.lastName
  return user.isVip ? `${fullName} (VIP)` : fullName
})

const expensiveTotal = computed(() => {
  return items
    .filter(i => i.price > 100)
    .reduce((sum, i) => sum + i.price, 0)
})
</script>
```

---

## 🎉 总结

### Computed 计算属性

- 📊 **作用**：基于已有数据计算新数据
- 💾 **缓存**：依赖不变，不重新计算
- ⚡ **性能**：比 methods 更高效
- 🔒 **默认只读**：不能直接赋值（除非定义 setter）

### Vue 2 vs Vue 3

| 特性 | Vue 2 | Vue 3 |
|------|-------|-------|
| **API 风格** | Options API | Composition API（可选） |
| **响应式原理** | Object.defineProperty | Proxy |
| **新增属性** | 需要 `$set` | 直接添加 ✅ |
| **数组索引** | 需要 `$set` | 直接修改 ✅ |
| **性能** | 较慢 | 更快 |
| **代码组织** | 按选项 | 按功能 |
| **逻辑复用** | Mixin | Composable |

### 最佳实践速记

```js
// 1. 基本类型用 ref，对象用 reactive
const count = ref(0)
const user = reactive({ name: 'Tom' })

// 2. Computed 只做计算，不要有副作用
const total = computed(() => price.value * quantity.value)

// 3. Watch 用于异步操作和副作用
watch(searchQuery, async (q) => { /* fetch data */ })

// 4. 避免解构 reactive
const { name } = toRefs(user)  // ✅
const { name } = user  // ❌

// 5. 提取可复用逻辑到 composables
const { count, increment } = useCounter()

// 6. 模板保持简洁，复杂逻辑用 computed
const displayText = computed(() => /* 复杂计算 */)
```

### 记忆口诀

```
Computed 有缓存，Methods 无缓存，
Ref 包基本，Reactive 包对象，
Vue 2 用 $set，Vue 3 直接改，
Computed 做计算，Watch 做副作用。
```

---

**恭喜你完成学习！** 🎊

现在你已经掌握了：
- ✅ Computed 计算属性的原理和使用
- ✅ Vue 2 Options API
- ✅ Vue 3 Composition API
- ✅ 响应式系统的区别
- ✅ 实战案例和最佳实践

下一步：
- 📖 阅读 [Vue 3 官方文档](https://cn.vuejs.org/)
- 💻 动手实现更多案例
- 🚀 在真实项目中应用所学知识

