# SwanLab 训练可视化使用指南

## 📖 概述

SwanLab 是一个开源的机器学习实验跟踪平台，专为模型训练可视化而设计。本平台已深度集成 SwanLab，提供完整的本地化部署和可视化解决方案。

## ✨ 功能特性

### 🎯 核心功能
- **本地化部署**: 完全本地运行，无需外部依赖
- **实时监控**: 实时查看训练指标和进度
- **可视化图表**: 损失函数、准确率、学习率等指标可视化
- **实验管理**: 创建、管理和比较不同的训练实验
- **结果保存**: 自动保存和分享训练结果

### 🛠️ 管理功能
- **服务管理**: 一键启动/停止 SwanLab 服务
- **配置管理**: 可视化配置服务参数
- **项目管理**: 创建、删除和管理训练项目
- **状态监控**: 实时监控服务状态和连接状态

## 🚀 快速开始

### 1. 自动安装

运行安装脚本自动安装和配置 SwanLab：

```bash
python install_swanlab.py
```

安装脚本会自动：
- 检查 Python 版本
- 安装 SwanLab 包
- 创建配置文件
- 创建数据目录
- 生成启动脚本

### 2. 手动安装

如果自动安装失败，可以手动安装：

```bash
# 安装 SwanLab
pip install swanlab

# 验证安装
swanlab --version
```

### 3. 启动服务

#### 方式一：使用启动脚本
```bash
./start_swanlab.sh
```

#### 方式二：在平台中启动
1. 进入"训练可视化"页面
2. 配置服务参数
3. 点击"启动 SwanLab"按钮

#### 方式三：命令行启动
```bash
swanlab ui --host localhost --port 5092 --data-dir ./swanlab_data
```

## 📱 界面使用

### 服务状态监控

在训练可视化页面，您可以查看：

- **服务状态**: 运行中、已停止、启动中、错误
- **访问地址**: 当前服务的访问URL
- **项目数量**: 已创建的训练项目数量

### 配置管理

可以配置以下参数：

- **服务地址**: 默认 localhost
- **端口**: 默认 5092
- **数据目录**: 训练数据存储路径
- **项目名称**: 默认项目名称

### 项目管理

#### 创建项目
1. 点击"新建项目"按钮
2. 输入项目名称和描述
3. 确认创建

#### 查看项目
- 点击项目卡片查看详情
- 显示创建时间、实验数量、最后更新时间
- 支持删除项目操作

## 🔧 高级配置

### 自定义数据目录

修改配置文件 `swanlab_config.json`：

```json
{
  "host": "localhost",
  "port": 5092,
  "data_dir": "/path/to/your/data",
  "project_name": "my_project"
}
```

### 网络配置

如果需要从其他机器访问：

```json
{
  "host": "0.0.0.0",
  "port": 5092,
  "data_dir": "./swanlab_data",
  "project_name": "modeltrain"
}
```

### 集成训练

在训练脚本中集成 SwanLab：

```python
import swanlab

# 初始化 SwanLab
swan = swanlab.init(
    project="modeltrain",
    experiment_name="experiment_1"
)

# 记录训练指标
for epoch in range(num_epochs):
    loss = train_epoch()
    accuracy = evaluate()
    
    swan.log({
        "epoch": epoch,
        "loss": loss,
        "accuracy": accuracy
    })

# 完成实验
swan.finish()
```

## 📊 可视化功能

### 支持的指标类型

- **损失函数**: 训练损失、验证损失
- **准确率**: 训练准确率、验证准确率
- **学习率**: 学习率变化曲线
- **梯度**: 梯度范数、梯度裁剪
- **自定义指标**: 任意数值指标

### 图表类型

- **折线图**: 时间序列数据
- **散点图**: 相关性分析
- **直方图**: 分布统计
- **热力图**: 矩阵数据
- **3D图表**: 多维数据

## 🛠️ 故障排除

### 常见问题

#### 1. 服务启动失败
```bash
# 检查端口占用
netstat -tulpn | grep 5092

# 检查 SwanLab 安装
swanlab --version

# 检查配置文件
cat swanlab_config.json
```

#### 2. 无法访问界面
- 检查防火墙设置
- 确认端口配置正确
- 验证服务状态

#### 3. 数据目录权限问题
```bash
# 设置目录权限
chmod 755 ./swanlab_data

# 检查磁盘空间
df -h
```

### 日志查看

查看 SwanLab 服务日志：

```bash
# 如果使用启动脚本
./start_swanlab.sh 2>&1 | tee swanlab.log

# 直接查看日志
tail -f swanlab.log
```

## 🔗 API 接口

### 后端 API

平台提供了完整的 SwanLab 管理 API：

- `GET /training/swanlab` - 获取服务信息
- `POST /training/swanlab/start` - 启动服务
- `POST /training/swanlab/stop` - 停止服务
- `POST /training/swanlab/config` - 保存配置
- `POST /training/swanlab/test` - 测试连接
- `GET /training/swanlab/projects` - 获取项目列表
- `POST /training/swanlab/projects` - 创建项目
- `DELETE /training/swanlab/projects/{name}` - 删除项目

### 前端 API

```javascript
import { trainingAPI } from '@/utils/api'

// 获取 SwanLab 信息
const info = await trainingAPI.getSwanLabInfo()

// 启动服务
await trainingAPI.startSwanLab(config)

// 创建项目
await trainingAPI.createSwanLabProject(project)
```

## 📚 参考资料

- [SwanLab 官方文档](https://docs.swanlab.ai/)
- [SwanLab GitHub](https://github.com/swanlab-ai/swanlab)
- [训练可视化最佳实践](https://docs.swanlab.ai/guides/best-practices)

## 🤝 技术支持

如果遇到问题，可以：

1. 查看本文档的故障排除部分
2. 检查 SwanLab 官方文档
3. 提交 Issue 到项目仓库
4. 联系技术支持团队

---

**注意**: 本指南基于 SwanLab 最新版本编写，如有版本差异请参考官方文档。 