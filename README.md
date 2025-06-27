# 企业模型训练平台

一个基于 Vue.js + FastAPI 的企业级模型训练和测试平台，集成 LlamaFactory 和 SwanLab，提供完整的模型训练生命周期管理。

## ✨ 功能特性

### 🎯 核心功能
- **用户系统**: 完整的注册/登录/权限管理，支持普通用户和管理员角色
- **模型对话**: ChatGPT风格的对话界面，支持会话历史和导出
- **模型测试**: 支持多模型对比测试，图像上传，流式/标准输出模式
- **模型训练**: 深度集成LlamaFactory，可视化参数配置，实时训练监控
- **训练可视化**: 本地部署SwanLab，实时查看训练效果和指标
- **系统管理**: 提示词管理，用户管理，模型VLLM加载/卸载

### 🏗️ 技术架构
- **前端**: Vue.js 3 + Element Plus + Vuex + Vue Router
- **后端**: FastAPI + SQLAlchemy + SQLite  
- **模型训练**: LlamaFactory + VLLM + SwanLab
- **认证方式**: 基于Passlib的密码哈希，无复杂JWT Token

## 📁 项目结构

```
modeltrain/
├── frontend/                 # Vue.js 前端应用
│   ├── src/
│   │   ├── views/           # 页面组件
│   │   │   ├── Login.vue    # 登录页面
│   │   │   ├── Dashboard.vue # 仪表板
│   │   │   ├── ModelChat.vue # 模型对话
│   │   │   ├── ModelTest.vue # 模型测试
│   │   │   ├── ModelTraining.vue # 模型训练
│   │   │   ├── SystemPrompt.vue # 系统提示词
│   │   │   ├── SwanLabViz.vue # SwanLab可视化
│   │   │   └── AdminPanel.vue # 管理员面板
│   │   ├── router/          # 路由配置
│   │   ├── store/           # Vuex状态管理
│   │   ├── utils/           # 工具函数
│   │   └── assets/          # 静态资源
│   └── package.json
├── backend/                  # FastAPI 后端服务
│   ├── app/
│   │   ├── api/             # API路由
│   │   │   ├── auth.py      # 认证相关API
│   │   │   ├── chat.py      # 聊天相关API
│   │   │   ├── model.py     # 模型管理API
│   │   │   ├── training.py  # 训练相关API
│   │   │   └── admin.py     # 管理员API
│   │   ├── models/          # 数据库模型
│   │   │   ├── user.py      # 用户模型
│   │   │   ├── chat.py      # 聊天模型
│   │   │   ├── training.py  # 训练模型
│   │   │   └── model.py     # 模型信息
│   │   ├── schemas/         # Pydantic模式
│   │   ├── utils/           # 工具函数
│   │   └── database.py      # 数据库配置
│   └── main.py              # 主应用入口
├── requirements.txt          # Python依赖包
├── start.bat                # Windows启动脚本
├── start.sh                 # Unix/Linux启动脚本
└── README.md
```

## 🚀 快速开始

### 环境要求
- Python 3.8+ (推荐 3.11 或 3.12)
- Node.js 16+ (推荐 18+)
- 至少8GB可用内存 (推荐16GB用于模型训练)
- GPU支持 (可选，用于加速训练)

### 一键启动
```bash
python start.py
```

### 手动启动

#### 后端服务
```bash
cd backend
pip install -r ../requirements.txt
python main.py
```
服务将在 `http://localhost:8000` 启动

#### 前端应用
```bash
cd frontend
npm install
npm run dev
```
应用将在 `http://localhost:5173` 启动

## 👤 默认账号

### 管理员账号
- **用户名**: admin
- **密码**: admin
- **权限**: 全部功能 + 用户管理

### 测试账号
首次启动后，可通过注册页面创建普通用户账号

## 📚 API文档

启动后端服务后，访问以下地址查看API文档：
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 🔧 配置说明

### 数据库
- 使用SQLite作为默认数据库
- 数据库文件: `backend/app.db`
- 首次启动自动创建表结构和管理员账号

### 文件上传
- 数据集文件存储: `backend/uploads/datasets/`
- 测试图片存储: `backend/uploads/images/`
- 模型文件存储: `backend/uploads/models/`

### LlamaFactory集成
项目预留了与LlamaFactory的集成接口，实际训练时会调用相关脚本：
- 训练脚本调用点: `backend/app/api/training.py`
- 参数配置: 通过前端界面设置训练参数
- 实时监控: 集成SwanLab进行训练可视化

## 🛠️ 开发说明

### 依赖说明
本项目使用宽松的版本依赖策略，确保与最新Python版本兼容：

**Web框架核心依赖**:
- `fastapi`, `uvicorn`: Web框架和ASGI服务器
- `sqlalchemy`: 数据库ORM
- `pydantic`: 数据验证和序列化
- `passlib[bcrypt]`: 密码哈希处理
- `python-multipart`, `aiofiles`: 文件上传和异步文件操作

**数据处理依赖**:
- `pandas`, `numpy`: 数据处理和科学计算
- `requests`: HTTP客户端

**深度学习和训练依赖** (核心功能):
- `torch`: PyTorch深度学习框架
- `transformers`: Hugging Face模型库
- `datasets`: 数据集处理
- `accelerate`: 分布式训练加速
- `peft`, `trl`: 参数高效微调和强化学习
- `bitsandbytes`: 量化训练支持

**模型推理和可视化**:
- `vllm`: 高性能模型推理引擎
- `swanlab`: 训练过程可视化

**版本策略**:
- 使用 `>=` 而非 `==` 确保可以安装最新兼容版本
- 最低版本要求确保功能完整性
- 兼容Python 3.8-3.12

### 自定义开发
1. **添加新的API**: 在 `backend/app/api/` 下创建新的路由文件
2. **添加数据模型**: 在 `backend/app/models/` 下定义新的数据库模型
3. **添加前端页面**: 在 `frontend/src/views/` 下创建新的Vue组件
4. **修改路由**: 更新 `frontend/src/router/index.js`

## 🔍 故障排除

### 常见问题
1. **Python脚本启动失败**: 确保使用Python 3.8+版本运行 `python start.py`
2. **Redis自动启动**: 某些Python深度学习包可能会自动启动Redis，这是正常现象，不影响项目运行
3. **端口占用**: 修改 `backend/main.py` 中的端口号
4. **数据库权限**: 确保对项目目录有写权限  
5. **依赖安装失败**: 使用国内镜像源安装pip包
6. **前端启动失败**: 检查Node.js版本是否符合要求

### 日志查看
- 后端日志: 控制台输出
- 前端日志: 浏览器开发者工具
- 数据库: 查看 `backend/app.db` 文件

## 📄 许可证

MIT License - 详见 LICENSE 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

> 💡 **提示**: 这是一个演示项目，展示了现代企业级应用的完整开发流程。可根据实际需求进行功能扩展和定制化开发。 