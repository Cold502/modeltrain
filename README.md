# 企业模型训练平台

企业模型训练平台是一套面向内部团队的模型配置、对话测试与训练管理解决方案。项目采用 Vue 3 + Element Plus 构建单页前端，后端基于 FastAPI 与 SQLAlchemy，内置 JWT 鉴权、模型配置中心与训练任务管理，并提供 SwanLab 监控入口。

> 文档正在分段更新。每个章节都会同步校对代码仓库中的实现，保证描述与实际行为一致。历史内容如果尚未覆盖，请暂时参考旧版说明。

## 功能概览（已核对代码）

- **账号体系**：邮箱/昵称注册、密码登录、Token 刷新与登出（Refresh Token 通过 HttpOnly Cookie 保存，`COOKIE_SECURE` 控制安全策略），管理员角色支持用户管理和统计汇总，并基于 JWT（详见 `backend/app/api/auth.py`、`backend/app/utils/auth.py`、`backend/app/api/admin.py`），支持刷新令牌 Cookie 自动续期。
- **前端认证**：Axios 拦截器与 Token 管理统一封装在 `frontend/src/utils/api.js`、`frontend/src/utils/tokenManager.js`，处理 401 重试、失败队列回放与 SSE 流式请求（含刷新重试、`processSSEResponse` 增量解码），`tokenManager.js` 还提供 `authenticatedFetch` 封装；`frontend/src/views/Login.vue`、`frontend/src/views/Register.vue`、`frontend/src/views/ResetPassword.vue` 提供登录/注册/找回密码表单，默认展示管理员账号提示，并在提交前清理旧凭证、表单校验通过后延迟导航反馈。
- **模型配置中心**：统一维护不同提供商的接入信息，可从 API 拉取模型列表，并保存为可复用的配置模板（系统启动时会注入一批禁用状态的默认模板；接口提供刷新模型、预置 `debug_refresh.log` 调试），详见 `backend/app/api/model_config.py`。
- **模型启用逻辑**：前端在 `frontend/src/views/ModelConfig.vue` 保存模型配置时，会在必填项通过 Element Plus 表单校验后自动将 `status` 置为 `1`，以便 playground(模型测试) 通过 `GET http://127.0.0.1:8000/api/model-config/` 拉取时识别为可用项。
- **对话与提示词**：支持面向指定模型配置的对话、流式返回、历史会话保存与导出，内置系统提示词库、格式验证与格式转换；前端通过 SSE 解析程序实时渲染 `<think>` 思维链，并结合 `thinkParser.js` 做补全/分层解析，`tokenManager.js` 负责 SSE 逐块聚合（`processSSEResponse`）和错误兜底（`[DONE]`、`[ERROR]` 标记）（`backend/app/api/chat.py`、`backend/app/services/prompt_service.py`、`frontend/src/views/ModelChat.vue`、`frontend/src/utils/thinkParser.js`、`frontend/src/utils/tokenManager.js`）。
- **模型测试**：提供批量模型对比测试、图片上传与结果留存，支持普通/流式模式与视觉模型输入。Playground 接口复用聊天能力但不落库，最多同时对比 3 个模型并实时展示 `<think>` 推理链（`frontend/src/views/ModelTest.vue`、`backend/app/api/model.py`、`backend/app/api/playground.py`）。
- **模型运行管理**：通过 `/api/model` 维护 VLLM 模型记录，支持模拟加载/卸载状态、添加自定义模型并持续保存测试历史（`backend/app/api/model.py`）。
- **模型对话链路**：`backend/app/api/chat.py` 负责 `/api/chat/sessions`, `/api/chat/sessions/{id}`, `/api/chat/messages` 等 REST 接口；前端 `frontend/src/views/ModelChat.vue` 在发送消息前先执行 Element Plus 表单校验（必填：选择模型、输入内容），随后调用 `chatAPI.createSession()`/`chatAPI.sendMessage()` 将用户消息持久化到数据库；普通模式使用 `POST http://127.0.0.1:8000/api/chat/`（后端会解析 `<think>`），流式模式通过 `POST http://127.0.0.1:8000/api/playground/chat/stream`（SSE）获取增量内容，最后统一在 `sendMessage` 中将完整的助手回复写回 `/api/chat/messages`，保证历史记录完整。
- **训练与监控**：允许上传数据集、创建训练任务、管理 SwanLab 服务；当前训练启动逻辑仅更新状态，实际训练需结合企业内部脚本，SwanLab 接口目前主要提供配置与模拟状态（配置写入 `swanlab_config.json`、支持本地进程启动/停止），并暴露健康检查端点（`/health`）供部署使用；前端 `ModelTraining.vue` 暂为占位说明页（`backend/app/api/training.py`、`frontend/src/views/ModelTraining.vue`、`backend/main.py`、`backend/app/api/playground.py`）。
- **训练可视化**：`frontend/src/views/SwanLabViz.vue` 对接 `/api/training/swanlab/*`，展示 SwanLab 服务状态、项目列表并提供一键启动、配置保存与连接测试。
- **数据模型**：核心 ORM 模型定义在 `backend/app/models/*`（用户/聊天/模型配置/模型测试/训练任务等），对应的 Pydantic Schema 位于 `backend/app/schemas/*`，保持字段别名与下划线同步，二者共同支撑 API 输入输出。
- **工具层**：鉴权、提示词、LLM 适配等通用能力集中在 `backend/app/utils`（JWT 令牌签发、默认管理员初始化）、`backend/app/services/prompt_service.py`（提示词模板/格式转换）、`backend/app/llm_core`（统一 LLM 客户端基类 `BaseClient`、厂商路由 `LLMClient`、OpenAI/Ollama 具体实现、推理链 `<think>` 解析与流式回退逻辑；可通过 `MODEL_PROVIDERS` 配置是否强制 API Key 与端点兼容），前端 `frontend/src/utils/api.js` 则统一封装 Axios 实例、模块化 API 入口与分类调用；入口 `backend/main.py` 统一加载 `.env`、注册 CORS、全局异常处理与健康检查。
- **系统管理**：管理员可查看用户列表、调整角色、删除账号并获取基础统计信息（`backend/app/api/admin.py`）。
- **前端布局与状态**：`frontend/src/components/Layout.vue` 负责主界面框架，支持折叠侧边栏、暗色模式切换（状态存储于 Vuex）；`frontend/src/store/index.js` 守护全局登录态/会话列表/暗色模式并提供 `loadUserFromStorage`、`toggleDarkMode` 等动作；`frontend/src/components/AuthNavbar.vue` 为认证页面复用的顶部导航，`frontend/src/components/ProviderIcon.vue` 提供模型提供商图标渲染。
- **暗色模式**：支持日间/黑夜模式无缝切换，颜色配置集中在 `frontend/src/assets/styles/main.css` 的 CSS 变量（`:root` 定义日间主题，`.dark-mode` 定义黑夜主题），状态通过 Vuex 持久化至 `localStorage`，全局切换由 `toggleDarkMode` 动作触发并自动应用 `.dark-mode` 类至 `document.documentElement`；切换开关位于 `Layout.vue` 和 `AuthNavbar.vue`，提供月亮/太阳图标指示当前模式（详见 `frontend/src/store/index.js`、`frontend/前端教程.md`）。
- **提示词管理**：`frontend/src/views/SystemPrompt.vue` 内置筛选、格式验证与模板转换，直接调用 `/api/chat/system-prompts`、`/convert`、`/validate`，支持预定义模板一键导入。
- **模型配置中心（前端）**：`frontend/src/views/ModelConfig.vue` 提供可视化卡片、状态标签与 Provider 图标，可刷新远端模型列表、直达测试场并通过对话框新增/编辑配置；其数据缓存在 Vuex 模块 `frontend/src/store/modules/model.js` 中，支持本地存储同步、按提供商分组、过滤可用模型配置与刷新远端模型。
- **管理员面板**：`frontend/src/views/AdminPanel.vue` 汇总系统统计、支持角色切换与用户删除操作，调用 `/api/admin/users`、`/stats`、`/users/{id}` 等接口，保护默认管理员。
- **仪表盘总览**：`frontend/src/views/Dashboard.vue` 聚合模型、训练任务、会话与数据集统计，依赖 `/api/model`、`/api/training`、`/api/chat` 拉取实时数据，快速导航至核心能力。

## 技术栈（参考项目依赖）

- **前端**：Vue 3、Vite、Element Plus、Vuex、Vue Router。
- **后端**：FastAPI、SQLAlchemy 2.x、Alembic、httpx、PyJWT、passlib。
- **数据库**：SQLite（默认），可通过 SQLAlchemy 切换其他后端。
- **可视化/工具**：SwanLab（训练监控）、Axios（前端 HTTP 客户端）。

## 📁 项目结构

```
modeltrain/
├── backend/
│   ├── app/
│   │   ├── api/                # 业务路由（auth/chat/model/model_config/playground/training/admin）
│   │   ├── models/             # SQLAlchemy 模型定义
│   │   ├── schemas/            # Pydantic 模型
│   │   ├── services/           # 业务服务（提示词等）
│   │   ├── utils/              # 工具方法（鉴权等）
│   │   ├── llm_core/           # LLM 客户端封装
│   │   └── database.py         # 会话工厂与 Base
│   ├── main.py                 # FastAPI 入口
│   └── requirements.txt        # 后端依赖清单
├── frontend/
│   ├── src/
│   │   ├── views/              # 页面组件（Dashboard/ModelChat/ModelTest/...）
│   │   ├── components/         # 通用组件
│   │   ├── store/              # Vuex 模块
│   │   ├── router/             # 前端路由
│   │   └── utils/              # 前端工具（API 客户端、token 管理）
│   ├── package.json
│   └── vite.config.js
├── ARCHITECTURE_SUMMARY.md
├── README.md
├── improve.md
└── 数据库修改后迁移命令.md
```

## 🚀 快速开始（开发环境）

### 环境准备
- 安装 Python 3.14（当前环境按 3.14 通过，建议保持一致）。
- 安装 Node.js 24.10.0（自带 npm 10.x）并确认 `npm -v` 输出匹配。
- 确保主机具备至少 32 GB 可用内存，推荐使用 NVMe SSD 以加速数据读写。
- 准备具备 ≥24 GB 显存的 GPU（如 RTX 4090 / A6000），用于运行大模型推理或微调。

### 后端启动（开发模式）

```bash
cd backend
python -m venv .venv
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
# macOS/Linux
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

服务默认监听 `http://127.0.0.1:8000`，所有业务接口位于 `/api/*`。

### 前端启动（开发模式）

```bash
cd frontend
npm install
npm run dev -- --host 127.0.0.1 --port 5173
```

Vite Dev Server 默认暴露在 `http://127.0.0.1:5173`，需跨域访问后端，请保持 `backend/main.py` 中 `allow_origins` 包含该地址。

## 👤 默认账号

### 管理员账号
- **用户名**: admin
- **密码**: admin
- **权限**: 全部功能 + 用户管理

### 测试账号
首次启动后，可通过注册页面创建普通用户账号

## 📚 API 文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 训练与推理概览

### 数据库
- 使用 SQLite 作为默认数据库
- 数据库文件: `backend/modeltrain.db`
- FastAPI 通过依赖注入方式获取 `SessionLocal`
- 使用 Alembic 管理数据库迁移；首次运行或更新结构后执行 `alembic upgrade head`，详细操作见《数据库修改后迁移命令.md》

### 文件上传
- 数据集文件存储: `backend/uploads/datasets/`
- 测试图片存储: `backend/uploads/images/`
- 模型文件存储: `backend/uploads/models/`

### 训练与推理集成
- 训练任务：上传数据集、创建任务、标记启动（`backend/app/api/training.py`），当前实现未直接调用 LlamaFactory，需要结合企业自有执行脚本。
- SwanLab：用于训练过程监控，可通过接口启动/停止本地 SwanLab watcher。
- 模型推理：通过 `LLMClient` 统一适配多个推理提供商（OpenAI、Ollama、DeepSeek、vLLM 等）。
- 应用启动阶段会自动创建默认管理员账号，并初始化一批模型配置模板。
- 模型配置支持从提供商端拉取模型列表（Ollama/OpenAI 等兼容接口），并将结果持久化到 `provider_models` 表。

### 模型提供商配置（示例参考）

#### 1. OpenAI
```
提供商: openai
端点: https://api.openai.com/v1/
API Key: sk-xxx...
模型: gpt-4o, gpt-4o-mini
```

#### 2. Ollama
```
提供商: ollama
端点: http://127.0.0.1:11434/api
API Key: (不需要)
模型: llama2, qwen, 等本地模型
```

#### 3. DeepSeek
```
提供商: deepseek
端点: https://api.deepseek.com/v1/
API Key: sk-xxx...
模型: deepseek-chat, deepseek-reasoner
```

#### 4. 硅基流动
```
提供商: siliconcloud
端点: https://api.siliconflow.cn/v1/
API Key: sk-xxx...
模型: Qwen2.5-7B-Instruct, deepseek-ai/DeepSeek-V3
```

## 开发约定

### 依赖说明

- 后端依赖集中在 `backend/requirements.txt`，当前锁定版本采用 `==` 以保证环境一致性，主要包含 FastAPI、SQLAlchemy、Alembic、httpx、PyJWT、passlib、swanlab 等。
- 前端依赖记录在 `frontend/package.json`，核心库为 Vue 3、Element Plus、Vue Router、Vuex、Axios、Vite。

### 自定义开发
1. **添加新的API**: 在 `backend/app/api/` 下创建新的路由文件
2. **添加数据模型**: 在 `backend/app/models/` 下定义新的数据库模型
3. **添加前端页面**: 在 `frontend/src/views/` 下创建新的Vue组件
4. **修改路由**: 更新 `frontend/src/router/index.js`

## 故障排查

### 常见问题
1. **依赖安装失败**：确认已激活虚拟环境；需要 Microsoft C++ Build Tools 以编译 `bcrypt`。
2. **`uvicorn` 启动端口占用**：修改 `backend/main.py` 或启动命令中的 `port`。
3. **跨域失败**：检查前端访问域名是否已添加到 `backend/main.py` 的 `allow_origins`。
4. **Token 自动刷新失效**：确保浏览器允许跨站 Cookie；后端环境变量 `COOKIE_SECURE` 在本地应置为 `false`。
5. **SwanLab 启动失败**：确认 `swanlab` 已安装于当前 Python 环境；若在 base 环境运行需使用 `python -m swanlab`。

### 日志查看
- 后端日志: 控制台输出
- 前端日志: 浏览器开发者工具
- 数据库: 查看 `backend/modeltrain.db`

## 版本规划（节选）

- 近期：补充训练任务执行能力、为敏感接口增加限流；完善 admin 模块功能说明。
- 中期：根据 `ARCHITECTURE_SUMMARY.md` 梳理的清单整合生命周期管理至 lifespan，并完善错误响应统一模板。
- 长期：考虑迁移状态管理到 Pinia，优化前端打包体积，引入 ESLint/Prettier 规范。
- 更多潜在优化项可参考 `improve.md` 文档。

## 🛠️ 技术架构与约定

- 后端采用标准的 FastAPI 分层结构，`api` 负责路由声明，`models`/`schemas` 区分 ORM 与 Pydantic，`services` 封装业务逻辑，`utils` 提供通用工具。
- LLM 能力通过 `app/llm_core` 提供统一客户端入口，OpenAI/Ollama/vLLM 等提供商在此聚合，向上游返回统一数据结构。
- 前端以 Vite + Vue 3 单页应用为主体，Vuex 持久化用户状态与 Token（`src/store/index.js`），模型配置缓存与过滤逻辑封装在 `src/store/modules/model.js`，`src/utils/api.js` 提供 Axios 拦截器与 API 封装，`src/utils/thinkParser.js` 统一解析 `<think>` 思维链。
- 关键数据目录：上传文件位于 `backend/uploads/*`，训练输出位于 `backend/outputs/training`，SQLite 数据库文件为 `backend/modeltrain.db`。

## 🌓 黑暗模式

### 颜色配置文件
所有主题颜色定义在 `frontend/src/assets/styles/main.css`：
- **日间模式**：`:root` 选择器（第2-79行）定义浅色主题变量
- **黑夜模式**：`.dark-mode` 类（第82-151行）定义深色主题变量

### 主题变量示例

#### 日间模式核心变量
```css
:root {
  --primary-blue: #64a8db;        /* 主色调 */
  --background-blue: #f0f8ff;     /* 页面背景 */
  --text-color: #333333;          /* 文字颜色 */
  --bg-color: #ffffff;            /* 组件背景 */
  --border-color: #e8f4fd;        /* 边框颜色 */
}
```

#### 黑夜模式核心变量
```css
.dark-mode {
  --primary-blue: #5a9bd4;        /* 主色调（较亮） */
  --background-blue: #1a1f26;     /* 深色页面背景 */
  --text-color: #e4e7ed;          /* 浅色文字 */
  --bg-color: #1d1e1f;            /* 深色组件背景 */
  --border-color: #414243;        /* 深色边框 */
}
```

### 切换机制
1. **状态管理**：模式状态存储在 Vuex (`frontend/src/store/index.js`)
2. **持久化**：通过 `localStorage.setItem('darkMode', 'true/false')` 保存用户偏好
3. **全局应用**：切换时自动添加/移除 `document.documentElement.classList` 中的 `dark-mode` 类
4. **UI 入口**：
   - 主界面：`Layout.vue` 右上角月亮/太阳图标切换
   - 登录页：`AuthNavbar.vue` 顶部导航栏切换

### 自定义颜色
编辑 `frontend/src/assets/styles/main.css`，修改对应的 CSS 变量即可全局生效。例如：

```css
.dark-mode {
  --background-blue: #0d1117;  /* GitHub 风格深色 */
  --bg-color: #161b22;
  --primary-blue: #58a6ff;     /* 更亮的蓝色强调 */
}
```

更多实现细节请参考 `frontend/前端教程.md` 的"黑暗模式实现原理"章节。

## 🎯 使用指南

### 1. 配置模型
1. 打开“模型配置”，浏览预置模板或从提供商 API 同步模型列表。
2. 填写提供商、端点、API Key、模型标识等信息，保存后会生成唯一配置 ID。
3. 可编辑温度、最大 Token、Top-P、Top-K 等推理参数，前端会校验数值范围。

### 2. 创建对话/测试
1. 在“模型对话”页选择目标模型配置，输入消息可选择是否启用流式返回。
2. 会话记录与消息历史保存在 `chat_sessions`、`chat_messages` 表，可随时导出。
3. “模型测试”页支持一次选择最多 3 个模型配置并行对比，结果会写入 `model_tests` 表。

### 3. 管理训练任务
1. 在“模型训练”页上传数据集文件（JSON/JSONL/CSV/TXT）。
2. 创建训练任务时选择数据集、目标模型名称及输出目录，会记录在 `training_tasks`。
3. 当前“开始训练”按钮仅更新任务状态，实际训练逻辑需接入企业内部脚本后再补全。

> 提示词功能：系统提示词可在“Prompt 管理”页创建与维护，后端默认使用 `created_by=1` 作为系统模板拥有者，部署时可结合登录态调整归属。

