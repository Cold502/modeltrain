## 未完成清单（精简版）

- 切换 FastAPI lifespan：将启动/关闭逻辑统一到 lifespan 上下文。
- 统一错误响应模型：在 `app/schemas/common.py` 定义错误模型，并在全局异常处理中返回统一结构。
- 登录限流/失败冷却：为敏感接口增加简单限流或失败计数与冷却时间。
- 生产 CORS 收敛：在生产环境缩减 `allow_headers/expose_headers`。
- 路由懒加载与代码分割：减少首屏包体体积。
- 前端规范化：ESLint/Prettier 与提交钩子。
- 中长期：Pinia 迁移或优化 Vuex 模块边界。

说明：以上为后续可实施项；其余内容已落实或合并至代码与专用文档。


