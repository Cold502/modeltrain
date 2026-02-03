# -*- coding: utf-8 -*-
"""优化论文第三章系统总体设计的脚本"""

def optimize_chapter3():
    file_path = r'd:\Desktop\modeltrain\论文第二版.txt'
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 优化1: 业务流程图开头
    content = content.replace(
        '本系统的核心业务流程围绕大模型的全生命周期展开，主要包括模型接入配置、对话推理应用和模型微调训练三大主线。',
        '本系统的核心业务流程围绕大语言模型的全生命周期管理展开，涵盖模型接入配置、对话推理应用和模型微调训练三条主要业务线。'
    )
    
    # 优化2: 模型接入配置流程
    content = content.replace(
        '1. **模型接入配置流程**：管理员登录 -> 进入模型配置中心 -> 添加/编辑提供商信息 -> 点击"刷新列表" -> 系统自动调用提供商API获取模型列表 -> 保存可用模型配置。',
        '1. **模型接入配置流程**\n管理员登录系统后进入模型配置中心，添加或编辑提供商基本信息（包括API密钥和基础URL），点击"刷新列表"按钮触发系统自动调用提供商API获取可用模型列表，最后保存模型配置信息。该流程实现了对异构模型提供商的统一接入管理。'
    )
    
    # 优化3: 对话推理应用流程
    content = content.replace(
        '2. **对话推理应用流程**：用户登录 -> 进入对话界面 -> 选择模型 -> 输入提示词 -> 系统根据路由策略调用对应模型API -> 接收SSE流式响应 -> 前端实时渲染回复及思维链。',
        '2. **对话推理应用流程**\n用户登录系统后进入对话界面，选择目标模型并输入提示词。系统根据模型路由策略调用对应的模型API，接收SSE（Server-Sent Events）流式响应数据，前端实时渲染模型回复内容。对于支持思维链（Chain of Thought）的模型，系统还会解析并展示推理过程。'
    )
    
    # 优化4: 模型微调训练流程
    content = content.replace(
        '3. **模型微调训练流程**：用户上传数据集 -> 数据格式校验 -> 创建训练任务 -> 配置训练参数（LoRA/QLoRA） -> 启动训练 -> 系统调度GPU资源 -> 实时回传监控指标 -> 训练完成 -> 注册新模型版本。',
        '3. **模型微调训练流程**\n用户上传指令微调数据集后，系统自动进行格式校验。用户创建训练任务并配置训练参数（如LoRA秩、学习率、训练轮数等）。训练启动后，系统调度GPU计算资源执行微调任务，实时回传训练损失、学习率等监控指标至前端。训练完成后，系统自动注册新的模型版本供后续使用。'
    )
    
    # 优化5: 系统逻辑架构图开头
    content = content.replace(
        '系统采用分层架构设计，自下而上分为基础设施层、数据存储层、核心服务层、接口网关层和用户交互层。',
        '系统采用经典的分层架构设计模式，自下而上划分为基础设施层、数据存储层、核心服务层、接口网关层和用户交互层五个逻辑层次。各层职责明确，耦合度低，便于系统维护和扩展。'
    )
    
    # 优化6: 系统结构图开头
    content = content.replace(
        '系统物理部署结构采用典型的微服务容器化部署方案。',
        '系统物理部署采用基于Docker的微服务容器化部署方案，各服务组件独立部署，通过容器编排实现统一管理。'
    )
    
    # 优化7: 前端容器描述
    content = content.replace(
        '- **前端容器**：运行Nginx，托管Vue 3构建的静态资源，代理后端API请求。',
        '- **前端容器**：运行Nginx Web服务器，托管Vue 3编译生成的静态资源文件，并作为反向代理转发后端API请求。'
    )
    
    # 优化8: 后端容器描述
    content = content.replace(
        '- **后端容器**：运行Uvicorn/Gunicorn，承载FastAPI应用，通过内部网络访问数据库。',
        '- **后端容器**：运行Uvicorn ASGI服务器（生产环境配合Gunicorn进行进程管理），承载FastAPI应用程序，通过Docker内部网络访问数据库服务。'
    )
    
    # 优化9: 数据库容器组描述
    content = content.replace(
        '- **数据库容器组**：包含MySQL、Redis、Qdrant容器，数据通过Docker Volume挂载持久化。',
        '- **数据库容器组**：包含MySQL关系型数据库、Redis缓存数据库、Qdrant向量数据库三个容器，数据文件通过Docker Volume挂载实现持久化存储。'
    )
    
    # 优化10: 训练工作节点描述
    content = content.replace(
        '- **训练工作节点**：配置NVIDIA GPU驱动和CUDA环境，运行LLaMA-Factory训练进程，与后端服务通过API或消息队列通信。',
        '- **训练工作节点**：配置NVIDIA GPU驱动和CUDA计算环境，运行LLaMA-Factory训练进程。训练节点与后端服务通过RESTful API或消息队列进行通信，实现训练任务的调度和监控数据的回传。'
    )
    
    # 优化11: 体系结构描述
    content = content.replace(
        '1. **体系结构**\n系统采用B/S（Browser/Server）架构，前后端分离开发。前端专注于界面渲染和交互逻辑，后端专注于业务逻辑处理和数据持久化，两者通过HTTP/HTTPS协议和JSON数据格式进行通信。对于实时性要求高的对话场景，采用SSE（Server-Sent Events）技术实现服务器向客户端的单向流式推送。',
        '1. **体系结构**\n系统采用B/S（Browser/Server）架构模式，遵循前后端分离的设计原则。前端负责界面渲染和用户交互逻辑，后端负责业务逻辑处理和数据持久化。两者通过HTTP/HTTPS协议进行通信，数据交换采用JSON格式。对于实时性要求较高的对话场景，系统采用SSE（Server-Sent Events）技术实现服务器向客户端的单向流式数据推送，保证用户体验的流畅性。'
    )
    
    # 优化12: 概念模型描述
    content = content.replace(
        '1. **概念模型（E-R图）**\n系统核心实体包括：用户（User）、模型提供商（Provider）、模型配置（ModelConfig）、会话（Session）、消息（Message）、训练任务（TrainingJob）、数据集（Dataset）。',
        '1. **概念模型（E-R图）**\n系统核心实体包括：用户（User）、模型提供商（Provider）、模型配置（ModelConfig）、会话（Session）、消息（Message）、训练任务（TrainingJob）、数据集（Dataset）等七个主要实体。实体间关系如下：'
    )
    
    # 优化13: 逻辑模型设计描述
    content = content.replace(
        '2. **逻辑模型设计**\n数据库设计遵循第三范式（3NF），所有表均包含`created_at`和`updated_at`时间戳字段，主键采用自增ID或UUID。',
        '2. **逻辑模型设计**\n数据库设计严格遵循第三范式（3NF）规范，确保数据冗余最小化和数据一致性。所有表均包含`created_at`（创建时间）和`updated_at`（更新时间）时间戳字段，便于数据审计和版本追踪。主键根据业务场景选用自增整型ID或UUID，保证数据唯一性。'
    )
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("第三章系统总体设计优化完成！")

if __name__ == '__main__':
    optimize_chapter3()
