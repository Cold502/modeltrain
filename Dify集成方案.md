# Dify集成方案

## 一、为什么选择Dify

Dify是国内领先的LLMOps平台，优势：
- 🚀 **完整的RAG功能**：文档上传、向量化、检索
- 🔄 **可视化工作流编排**：拖拽式Workflow设计
- 🤖 **Agent支持**：Function Calling、ReAct模式
- 💬 **多种应用类型**：对话/文本生成/Agent/工作流
- 🇨🇳 **国内认可度高**：中文文档完善，社区活跃
- 📦 **Git源码部署**：不依赖Docker

## 二、系统架构集成

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────┐
│                  前端 (Vue 3)                       │
├─────────────────────────────────────────────────────┤
│  对话页面  │  模型对比  │  Dify管理  │  训练页面    │
│  (增强)    │  (已有)    │  (新增)    │  (已有)      │
│  ↓判断     │            │  ↓iframe   │              │
│  RAG?工作流?│            │  Dify UI   │              │
└─────────────────────────────────────────────────────┘
       ↓                        ↓
┌─────────────────────────────────────────────────────┐
│              后端 (FastAPI)                         │
├─────────────────────────────────────────────────────┤
│  普通对话  │  Dify代理  │  健康检查  │  其他API     │
│  (已有)    │  (新增)    │  (新增)    │  (已有)      │
└─────────────────────────────────────────────────────┘
       ↓            ↓
┌──────────────┬──────────────┬──────────────┐
│    OpenAI    │     Dify     │LLaMA-Factory │
│  等LLM提供商 │  本地部署    │   训练平台   │
│              │  :5001       │   :7860      │
└──────────────┴──────────────┴──────────────┘
```

### 2.2 对话流程判断

```
用户发送消息
    ↓
前端判断是否选择了RAG/工作流
    ↓
┌─────────────┬─────────────┐
│  普通对话   │ RAG/工作流  │
│  ↓          │  ↓          │
│  调用后端   │  调用Dify   │
│  /chat      │  API代理    │
└─────────────┴─────────────┘
```

## 三、Dify源码部署（v1.11.4）

### 3.1 环境要求

- Python 3.10+
- Node.js 18+
- PostgreSQL 14+
- Redis 6+

### 3.2 部署步骤

#### Step 1: 克隆代码

```bash
# 克隆Dify仓库
git clone https://github.com/langgenius/dify.git
cd dify

# 切换到v1.11.4版本
git checkout tags/1.11.4 -b v1.11.4
```

#### Step 2: 后端部署

```bash
cd api

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env

# 编辑 .env 文件
# 必须配置：
# - SECRET_KEY=your-secret-key
# - DB_USERNAME=postgres
# - DB_PASSWORD=your-password
# - DB_HOST=localhost
# - DB_PORT=5432
# - DB_DATABASE=dify
# - REDIS_HOST=localhost
# - REDIS_PORT=6379
# - REDIS_PASSWORD=
# - VECTOR_STORE=qdrant  # 或 milvus/weaviate
# - QDRANT_URL=http://localhost:6333

# 初始化数据库
flask db upgrade

# 启动服务
flask run --host 0.0.0.0 --port 5001
```

#### Step 3: 前端部署

```bash
cd ../web

# 安装依赖
npm install

# 配置环境变量
cp .env.example .env.local

# 编辑 .env.local
# NEXT_PUBLIC_API_PREFIX=http://localhost:5001

# 开发模式启动
npm run dev
# 或生产构建
npm run build && npm run start
```

#### Step 4: 向量数据库部署（Qdrant推荐）

```bash
# 下载Qdrant
wget https://github.com/qdrant/qdrant/releases/download/v1.7.4/qdrant-x86_64-pc-windows-msvc.zip
unzip qdrant-x86_64-pc-windows-msvc.zip

# 启动Qdrant
./qdrant.exe
# 默认运行在 http://localhost:6333
```

### 3.3 配置PostgreSQL

```sql
-- 创建数据库
CREATE DATABASE dify;
CREATE USER dify_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE dify TO dify_user;
```

### 3.4 配置Redis

```bash
# Windows下载Redis
# https://github.com/tporadowski/redis/releases

# 启动Redis
redis-server
```

## 四、前端集成

### 4.1 创建Dify管理页面

```vue
<!-- frontend/src/views/DifyManage.vue -->
<template>
  <div class="dify-container">
    <div class="dify-header">
      <h2>Dify 应用管理</h2>
      <el-button @click="openDifyConsole" type="primary">
        打开Dify控制台
      </el-button>
    </div>
    
    <div class="dify-content">
      <iframe 
        :src="difyUrl" 
        frameborder="0"
        class="dify-iframe"
      />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const difyUrl = ref('http://localhost:3000')  // Dify前端地址

const openDifyConsole = () => {
  window.open(difyUrl.value, '_blank')
}
</script>

<style scoped>
.dify-container {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.dify-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.dify-content {
  flex: 1;
  overflow: hidden;
}

.dify-iframe {
  width: 100%;
  height: 100%;
}
</style>
```

### 4.2 修改对话页面（增加RAG/工作流判断）

```vue
<!-- frontend/src/views/Chat.vue 部分修改 -->
<template>
  <div class="chat-container">
    <!-- 顶部选项栏 -->
    <div class="chat-options">
      <el-radio-group v-model="chatMode">
        <el-radio label="normal">普通对话</el-radio>
        <el-radio label="rag">RAG检索</el-radio>
        <el-radio label="workflow">工作流</el-radio>
      </el-radio-group>
      
      <!-- RAG/工作流配置 -->
      <div v-if="chatMode !== 'normal'" class="dify-config">
        <el-select v-model="selectedDifyApp" placeholder="选择应用">
          <el-option 
            v-for="app in difyApps" 
            :key="app.id" 
            :label="app.name" 
            :value="app.id"
          />
        </el-select>
      </div>
    </div>
    
    <!-- 原有对话界面 -->
    <!-- ... -->
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { sendMessage, sendDifyMessage } from '@/utils/api'

const chatMode = ref('normal')
const selectedDifyApp = ref('')
const difyApps = ref([])

// 加载Dify应用列表
const loadDifyApps = async () => {
  try {
    const res = await fetch('http://localhost:5001/v1/apps', {
      headers: {
        'Authorization': `Bearer ${difyApiKey}`
      }
    })
    const data = await res.json()
    difyApps.value = data.data
  } catch (error) {
    console.error('加载Dify应用失败:', error)
  }
}

// 发送消息（根据模式调用不同API）
const handleSendMessage = async (message) => {
  if (chatMode.value === 'normal') {
    // 调用原有后端API
    await sendMessage(message)
  } else {
    // 调用Dify API
    await sendDifyMessage({
      app_id: selectedDifyApp.value,
      query: message,
      mode: chatMode.value
    })
  }
}
</script>
```

### 4.3 路由配置

```javascript
// frontend/src/router/index.js
{
  path: '/dify',
  name: 'DifyManage',
  component: () => import('@/views/DifyManage.vue'),
  meta: { 
    requiresAuth: true,
    title: 'Dify应用管理'
  }
}
```

### 4.4 导航菜单

```vue
<!-- frontend/src/components/Layout.vue -->
<el-menu-item index="/dify">
  <el-icon><Grid /></el-icon>
  <span>Dify应用</span>
</el-menu-item>
```

## 五、后端集成

### 5.1 Dify API代理

```python
# backend/app/api/dify_proxy.py
from fastapi import APIRouter, HTTPException, Depends, Header
from typing import Optional
import httpx
import os

router = APIRouter()

DIFY_API_URL = os.getenv("DIFY_API_URL", "http://localhost:5001")
DIFY_API_KEY = os.getenv("DIFY_API_KEY", "")

@router.post("/dify/chat")
async def chat_with_dify(
    app_id: str,
    query: str,
    mode: str = "rag",
    conversation_id: Optional[str] = None,
    user: str = "default_user"
):
    """
    代理Dify对话API
    
    mode: "rag" 或 "workflow"
    """
    try:
        async with httpx.AsyncClient() as client:
            # Dify Chat API
            url = f"{DIFY_API_URL}/v1/chat-messages"
            
            payload = {
                "inputs": {},
                "query": query,
                "response_mode": "streaming",
                "user": user,
                "conversation_id": conversation_id
            }
            
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}",
                "Content-Type": "application/json"
            }
            
            response = await client.post(url, json=payload, headers=headers)
            response.raise_for_status()
            
            return response.json()
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dify/apps")
async def get_dify_apps():
    """获取Dify应用列表"""
    try:
        async with httpx.AsyncClient() as client:
            url = f"{DIFY_API_URL}/v1/apps"
            headers = {
                "Authorization": f"Bearer {DIFY_API_KEY}"
            }
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dify/health")
async def check_dify_health():
    """检查Dify服务状态"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{DIFY_API_URL}/health", timeout=3)
            return {
                "status": "running" if response.status_code == 200 else "error",
                "url": DIFY_API_URL
            }
    except:
        return {
            "status": "stopped",
            "message": "Dify服务未启动"
        }
```

### 5.2 注册路由

```python
# backend/main.py
from app.api import dify_proxy

app.include_router(dify_proxy.router, prefix="/api/dify", tags=["Dify"])
```

## 六、配置文件

### 6.1 后端环境变量

```bash
# backend/.env 添加
DIFY_API_URL=http://localhost:5001
DIFY_API_KEY=your-dify-api-key
```

### 6.2 前端环境变量

```bash
# frontend/.env 添加
VITE_DIFY_URL=http://localhost:3000
```

## 七、使用流程

### 7.1 首次使用

1. 访问 `http://localhost:3000` 打开Dify控制台
2. 注册账号并登录
3. 创建应用：
   - **对话型应用**：用于RAG检索对话
   - **工作流应用**：用于复杂任务编排
4. 获取应用API Key，配置到后端

### 7.2 创建RAG应用

1. 在Dify中点击"创建应用"
2. 选择"对话型应用"
3. 添加知识库：
   - 上传文档（PDF/Word/TXT等）
   - 自动切片和向量化
4. 配置检索参数：
   - Top K、相似度阈值等
5. 发布应用，获取API Key

### 7.3 创建工作流应用

1. 创建"工作流应用"
2. 拖拽节点设计流程：
   - LLM节点、知识库检索、条件分支等
3. 配置节点参数
4. 测试并发布

## 八、优先级和时间规划

### P0 - Dify基础集成（2-3天）
- [x] ✅ 部署Dify服务（PostgreSQL + Redis + Qdrant + Dify）
- [ ] 前端创建DifyManage.vue iframe页面
- [ ] 修改Chat.vue添加模式选择
- [ ] 后端创建dify_proxy.py代理API
- [ ] 测试RAG对话功能

### P1 - 工作流集成（1-2天）
- [ ] 在Dify中创建示例工作流
- [ ] 前端工作流模式测试
- [ ] 前端展示工作流执行过程

### P2 - Agent增强（可选）
- [ ] Dify本身支持Agent，可直接使用
- [ ] 或者自己实现轻量级Agent集成Dify检索

## 九、端口规划

| 服务 | 端口 | 说明 |
|------|------|------|
| 前端（Vue） | 5173 | 开发模式 |
| 后端（FastAPI） | 8000 | API服务 |
| Dify API | 5001 | Dify后端 |
| Dify Web | 3000 | Dify前端 |
| PostgreSQL | 5432 | 数据库 |
| Redis | 6379 | 缓存 |
| Qdrant | 6333 | 向量数据库 |
| LLaMA-Factory | 7860 | 训练平台 |
| SwanLab | 5092 | 训练监控 |

## 十、注意事项

1. **Dify API Key管理**：
   - 每个应用独立的API Key
   - 存储在后端环境变量中
   - 不要暴露给前端

2. **资源占用**：
   - Dify + PostgreSQL + Redis + Qdrant
   - 建议至少16GB RAM
   - 如果资源不足，Qdrant可以换成内存模式

3. **数据隔离**：
   - Dify有独立的用户系统
   - 可以通过API的`user`参数区分用户

4. **性能优化**：
   - 向量检索缓存
   - API响应缓存
   - 控制并发请求数

## 十一、下一步行动

1. **立即开始**：部署Dify v1.11.4
2. **前端开发**：DifyManage.vue + Chat.vue修改
3. **后端开发**：dify_proxy.py API代理
4. **测试验证**：RAG对话 + 工作流执行
5. **文档完善**：使用手册和API文档
