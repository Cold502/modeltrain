# 企业模型训练平台 - 增强版

一个功能丰富的企业级模型训练和测试平台，支持多模型对比、流式输出、模型配置管理等功能。

## 🆕 新增功能

### 1. 模型配置管理
- **多提供商支持**: OpenAI、Ollama、DeepSeek、硅基流动、智谱AI等
- **参数调节**: 温度、最大Token、Top-P、Top-K等参数配置
- **模型类型**: 支持文本模型和视觉模型
- **配置验证**: 自动检测API Key和连接状态

### 2. 多模型测试对比
- **并行对比**: 最多同时选择3个模型进行对比测试
- **流式输出**: 支持实时流式响应显示
- **推理过程**: 显示模型的思维链(Chain of Thought)
- **图片支持**: 视觉模型支持图片上传和分析
- **响应模式**: 普通输出和流式输出两种模式

### 3. 统一LLM客户端
- **多提供商**: 统一的接口支持多种模型提供商
- **自动适配**: 根据提供商自动选择合适的客户端
- **错误处理**: 完善的错误处理和重试机制
- **思维链**: 支持推理过程的提取和显示

## 🚀 快速开始

### 环境要求
- Python 3.8+
- Node.js 16+
- npm 8+

### 一键启动
```bash
# 克隆项目
git clone <repository-url>
cd modeltrain

# 运行启动脚本
python start_new.py
```

启动脚本会自动：
- 检查系统依赖
- 创建Python虚拟环境
- 安装后端依赖
- 安装前端依赖
- 设置数据库
- 启动后端和前端服务

### 访问地址
- **前端**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

### 默认账号
- **管理员**: admin / admin
- **普通用户**: 可通过注册页面创建

## 📱 功能界面

### 1. 模型配置管理
![Model Config](docs/model-config.png)

- 添加和管理不同的模型配置
- 支持多种提供商和模型类型
- 实时配置状态显示
- 参数调节和测试

### 2. 多模型测试
![Model Test](docs/model-test.png)

- 最多3个模型并行对比
- 流式输出实时显示
- 推理过程可视化
- 图片上传支持

### 3. 智能对话
![Chat Interface](docs/chat.png)

- ChatGPT风格界面
- 历史对话管理
- 多模态支持
- 上下文记忆

## 🛠️ 技术架构

### 后端技术栈
- **FastAPI**: 现代Python Web框架
- **SQLAlchemy**: ORM数据库操作
- **SQLite**: 轻量级数据库
- **httpx**: 异步HTTP客户端
- **Pydantic**: 数据验证

### 前端技术栈
- **Vue.js 3**: 响应式前端框架
- **Element Plus**: UI组件库
- **Vite**: 构建工具
- **Axios**: HTTP客户端
- **Vue Router**: 路由管理

### LLM集成
- **统一接口**: 支持多种模型提供商
- **流式处理**: 实时响应流处理
- **错误恢复**: 自动重试和降级
- **推理链**: 思维过程提取

## 📁 项目结构

```
modeltrain/
├── backend/                 # 后端代码
│   ├── app/
│   │   ├── api/            # API路由
│   │   ├── models/         # 数据模型
│   │   ├── schemas/        # Pydantic模式
│   │   ├── llm_core/       # LLM核心模块
│   │   └── utils/          # 工具函数
│   ├── requirements.txt    # Python依赖
│   └── main.py            # 应用入口
├── frontend/               # 前端代码
│   ├── src/
│   │   ├── views/         # 页面组件
│   │   ├── components/    # 通用组件
│   │   ├── utils/         # 工具函数
│   │   └── router/        # 路由配置
│   ├── package.json       # 前端依赖
│   └── vite.config.js     # 构建配置
├── start_new.py           # 启动脚本
└── README_NEW.md          # 项目文档
```

## 🔧 配置说明

### 模型提供商配置

#### 1. OpenAI
```
提供商: openai
端点: https://api.openai.com/v1/
API Key: sk-xxx...
模型: gpt-4o, gpt-4o-mini
```

#### 2. Ollama (本地)
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

### 模型参数说明

- **温度 (Temperature)**: 0.0-2.0，控制输出的随机性
- **最大Token**: 1-32768，控制最大输出长度
- **Top-P**: 0.0-1.0，核采样参数
- **Top-K**: 0-100，候选词数量限制

## 🎯 使用指南

### 1. 配置模型
1. 进入"模型配置"页面
2. 点击"添加模型"
3. 选择提供商和配置参数
4. 保存配置

### 2. 测试模型
1. 进入"模型测试"页面
2. 选择1-3个模型进行对比
3. 选择输出模式（普通/流式）
4. 输入测试内容并发送
5. 查看并对比不同模型的响应

### 3. 上传图片测试
1. 配置至少一个视觉模型
2. 在测试页面选择视觉模型
3. 点击"上传图片"按钮
4. 发送消息进行图片分析

## 🔍 常见问题

### Q: 如何添加新的模型提供商？
A: 在`llm_core`模块中创建新的客户端类，继承`BaseClient`并实现相应方法。

### Q: 模型无法连接怎么办？
A: 检查网络连接、API Key有效性和端点配置是否正确。

### Q: 如何查看详细的错误信息？
A: 查看浏览器控制台或后端日志文件获取详细错误信息。

### Q: 支持哪些图片格式？
A: 支持常见图片格式：JPG, PNG, GIF, WebP等，最大5MB。

## 🤝 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🙏 致谢

- [FastAPI](https://fastapi.tiangolo.com/) - 现代Python Web框架
- [Vue.js](https://vuejs.org/) - 渐进式JavaScript框架
- [Element Plus](https://element-plus.org/) - Vue 3 UI组件库
- [easy-dataset](https://github.com/example/easy-dataset) - 模型对话功能参考

---

💡 **提示**: 如果您在使用过程中遇到任何问题，请查看API文档或提交Issue。 