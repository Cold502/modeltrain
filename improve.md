# improve.md

项目在梳理 README 时同步发现以下可以进一步优化或补强的点，按优先级分类列出，后续可据此规划迭代：

## 高优先级

1. **训练任务执行缺失**  
   - 目前 `backend/app/api/training.py` 的 `/tasks/{task_id}/start` 接口仅修改状态，未真正触发 LlamaFactory 或内部训练脚本。  
   - 需要补充任务调度/异步执行机制，至少提供可配置的命令行调用或 Celery/后台线程方案，同时写回训练日志。

2. **全局生命周期管理**  
   - `backend/main.py` 仍使用 `@app.on_event("startup")` 注册初始化逻辑，建议迁移到 FastAPI `lifespan` 上下文，便于统一处理资源释放（数据库连接、SwanLab 进程等）。

3. **认证与权限强化**  
   - 登录失败/刷新频繁请求缺少节流与黑名单机制；可在 `app/utils/auth.py` 或 `auth` 路由层增加失败计数、冷却策略，防止暴力破解。  
   - 管理员接口依赖 `is_admin` 字段，缺少基于角色的中间层装饰器，建议补充统一的权限校验函数。

## 中优先级

1. **配置安全与密钥管理**  
   - 默认将 API Key 明文存储在 `model_configs` 表；需评估加密存储或引入外部密钥管理（如环境变量映射、KMS）。

2. **前端状态管理与校验**  
   - Vuex store 中的用户 Token 依赖 localStorage，缺少失效容错；可在 `tokenManager` 中添加刷新失败时的统一降级。  
   - 项目尚未配置 ESLint/Prettier，建议按照 `ARCHITECTURE_SUMMARY.md` 的 TODO 引入代码规范及 pre-commit 钩子。

3. **Model Config 同步体验**  
   - `/model-config/models/refresh` 调用成功后日志写入 `debug_refresh.log`，但前端未显示详细错误；可以补充友好提示及接口重试策略。

## 低优先级

1. **认证表单与布局优化**  
   - 登录/注册/重置密码页面（`frontend/src/views/Login.vue`、`frontend/src/views/Register.vue`、`frontend/src/views/ResetPassword.vue`）默认清空本地 Token 并使用多个 `console.log` 调试语句，可在生产构建前移除，改用统一日志封装。  
   - `frontend/src/components/Layout.vue` 的暗色模式开关存在硬编码 UI，可考虑抽象为可复用组件，并补充无障碍提示。  
   - `frontend/src/components/AuthNavbar.vue` 与 `Layout.vue` 主题开关重复，可抽取公共组件并增加键盘焦点样式。  
   - 登录页将 refresh token 从 localStorage 删除，但后端改为 HttpOnly Cookie 后不再存储，可统一清理该键值。
   - 仪表盘统计组件（`frontend/src/views/Dashboard.vue`）缺少加载/失败反馈，建议在请求期间显示骨架或错误信息。
   - 提示词管理页（`frontend/src/views/SystemPrompt.vue`）大量使用 `navigator.clipboard` 和内联样式，建议封装统一工具并还原 Element 默认配色以提升可维护性。
   - 模型配置页（`frontend/src/views/ModelConfig.vue`）依赖 `store.dispatch('model/refreshModels')` 时缺少全局错误提示，可增加 message 反馈与禁用状态。
   - 管理员面板（`frontend/src/views/AdminPanel.vue`）接口失败时仅打印日志，可补充失败后禁用刷新按钮、展示重试提示，并考虑分页以缓解大数据量。
   - `frontend/src/components/ProviderIcon.vue` 访问 Store 读取暗色模式，可改为使用 props 或 provide/inject，避免组件在无 Store 场景报错。
   - `backend/app/utils/auth.py` 在模块导入时直接加载 `.env` 并实例化 `HTTPBearer`，可评估懒加载或集中化配置，避免重复读取环境；日志中文案偏口语化，可统一风格。
   - `backend/app/llm_core/llm_client.py` 的供应商列表写死在代码里，可改写为配置驱动或后端接口返回，方便扩展；`get_response_with_cot` 对 `<think>` 解析依靠正则，考虑抽出共用工具并处理嵌套标签。
   - `backend/app/api/chat.py`：系统提示词接口仍使用固定 `user_id=1`，应改为当前用户；流式响应缺少速率限制与错误码映射。
   - `backend/app/api/model_config.py`：默认 provider/config 列表体量较大，可拆分到独立模块或配置文件；刷新模型接口写大量日志到 `debug_refresh.log`，应考虑日志轮转并避免阻塞。
   - `backend/app/api/training.py`：SwanLab 进程管理依赖全局变量，若多进程部署可能失效；`requests` 同步调用与 FastAPI 异步混用，建议统一异步或在线程池执行。
    - `backend/app/api/auth.py`：登录/刷新流程缺少 IP/设备维度的安全控制，`COOKIE_SECURE` 应有默认 True/按环境自动切换；刷新接口手动解析 cookie，可抽成工具函数。
    - `backend/main.py`：CORS 白名单与日志级别硬编码，建议通过环境变量配置；`@app.on_event("startup")` 可迁移至 lifespan，避免未来弃用。
    - `backend/app/database.py`：`DATABASE_URL` 写死为本地 SQLite，建议读取环境变量并兼容不同部署；缺少连接池参数。
    - `backend/requirements.txt`：包含大量未使用的桌面/脚本依赖（PyAutoGUI、MouseInfo 等），应梳理用途或拆分 extra，避免冗余体积。
    - `backend/app/models` 与 `backend/app/schemas`：部分类字段仍使用 `user_id=1` 默认值或无软删除标记，可考虑增加归属与审计字段；Schema 大量 alias，可拆分公共基类减少重复。
    - `backend/app/llm_core`：`MODEL_PROVIDERS` 配置写死在代码中，建议迁移到数据库或配置文件并支持热加载；`DEFAULT_MODEL_SETTINGS` 未覆盖 top_k 以外的 sampling 参数，Stream 回退逐字符输出易阻塞。
    - `frontend/src/utils/tokenManager.js`：`refreshToken` 使用 `axios.post('/api/auth/refresh')`，当 `VITE_API_BASE_URL` 指向其他域名时会失效；Refresh 队列未处理请求体重播，`authenticatedFetch`/SSE 重试逻辑缺少失败兜底提示。
    - `frontend/src/utils/api.js`：模块化 API 方法依赖统一实例但无类型约束，错误处理对 5xx 静默，可补充系统提示与链路追踪 ID；`uploadImage` 等 multipart 请求未显式 `withCredentials`。
    - `frontend/src/store/index.js`：`loadUserFromStorage` 依赖全局 `window.location` 跳页，与路由器解耦不足，且多个 `console.log`/`console.error` 可迁移到 `logger`；暗色模式直接操作 DOM，可抽 Hooks/Directive 并兼容 SSR。
    - `frontend/src/store/modules/model.js`：本地缓存无版本控制，`refreshModels` 仅写 state 不提示用户；可增加错误消息与节流，`SET_MODEL_CONFIG_LIST` 始终覆盖 localStorage 易造成并发丢失。
    - `frontend/src/views/Login.vue`：大量调试日志输出敏感数据引用，可统一走 `logger.logSafe`；登录前清除 `refresh_token` 无意义；跳转前 `setTimeout` 依赖魔数，可改为路由守卫确认状态。
    - `frontend/src/views/Register.vue`：注册成功后固定 `setTimeout` 延迟跳转，建议使用 `await router.push` 并展示倒计时；缺少密码强度提示及隐私条款确认。
    - `frontend/src/views/ResetPassword.vue`：逻辑复用少、console 日志过多；错误提示读取 `error.response.data.detail` 与后端 `ErrorResponse` 不匹配，应解析 `error.error.message`。

2. **文档与脚本清理**  
   - 仓库 root 不再包含 `start.py`、`start.sh` 等脚本，确认后可彻底移除 README 中的旧提法，并考虑补充新的部署脚本示例。

---

本文档旨在记录与 README 重写过程中发现的改进点，可视化后续工作进度时建议同步更新此列表。

