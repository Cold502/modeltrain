# 企业模型训练平台 - Docker部署文档

## 📋 系统要求

- Docker Engine 20.10+
- Docker Compose 2.0+
- 至少16GB RAM
- 至少100GB可用磁盘空间
- （可选）NVIDIA GPU + nvidia-docker（用于模型训练）

## 🚀 快速开始

### 1. 克隆项目并配置环境变量

```bash
# 克隆项目
git clone <your-repo-url>
cd modeltrain

# 复制.env.example为.env
cp .env.example .env
```

**必须修改的环境变量**：
- `SECRET_KEY`: 修改为随机字符串
- `DIFY_API_KEY`: 在Dify中创建应用后获取
- `MYSQL_ROOT_PASSWORD`: 修改数据库密码
- `POSTGRES_PASSWORD`: 修改Dify数据库密码
- `REDIS_PASSWORD`: 修改Redis密码

### 2. 启动所有服务

```bash
# 构建并启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f
```

### 3. 初始化数据库

```bash
# 进入后端容器
docker exec -it modeltrain-backend bash

# 运行数据库迁移
alembic upgrade head

# 退出容器
exit
```

### 4. 访问服务

- **前端应用**: http://localhost
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs
- **Dify平台**: http://localhost:3000
- **LLaMA-Factory**: http://localhost:7860
- **SwanLab**: http://localhost:5092

## 📦 服务说明

### 核心服务

| 服务 | 端口 | 说明 |
|------|------|------|
| frontend | 80 | Vue3前端应用 |
| backend | 8000 | FastAPI后端服务 |
| mysql | 3306 | MySQL数据库 |

### 集成服务

| 服务 | 端口 | 说明 |
|------|------|------|
| llamafactory | 7860 | LLaMA-Factory训练界面 |
| swanlab | 5092 | SwanLab可视化 |
| dify-web | 3000 | Dify控制台 |
| dify-api | 5001 | Dify API服务 |

### 支撑服务

| 服务 | 端口 | 说明 |
|------|------|------|
| postgres | 5432 | Dify数据库 |
| redis | 6379 | Dify缓存 |
| qdrant | 6333 | 向量数据库 |

## 🔧 常用命令

### 服务管理

```bash
# 启动所有服务
docker-compose up -d

# 停止所有服务
docker-compose down

# 重启特定服务
docker-compose restart backend

# 查看服务日志
docker-compose logs -f backend

# 进入容器
docker exec -it modeltrain-backend bash
```

### 数据管理

```bash
# 备份MySQL数据
docker exec modeltrain-mysql mysqldump -u root -p modeltrain > backup.sql

# 恢复MySQL数据
docker exec -i modeltrain-mysql mysql -u root -p modeltrain < backup.sql

# 清理所有数据（危险操作！）
docker-compose down -v
```

### 更新服务

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose up -d --build

# 查看服务状态
docker-compose ps
```

## 🐛 故障排查

### 常见问题

#### 1. 端口冲突

```bash
# 检查端口占用
netstat -tuln | grep <port>

# 修改docker-compose.yml中的端口映射
```

#### 2. 服务启动失败

```bash
# 查看详细日志
docker-compose logs <service-name>

# 检查服务健康状态
docker-compose ps
```

#### 3. 数据库连接失败

```bash
# 确认数据库服务已启动
docker-compose ps mysql

# 检查环境变量配置
docker exec modeltrain-backend env | grep DATABASE_URL

# 测试数据库连接
docker exec -it modeltrain-mysql mysql -u root -p
```

#### 4. GPU不可用（LLaMA-Factory）

```bash
# 检查nvidia-docker是否安装
docker run --rm --gpus all nvidia/cuda:11.8.0-base-ubuntu22.04 nvidia-smi

# 如无GPU，移除docker-compose.yml中的GPU配置
```

## 🔐 安全建议

1. **生产环境必须修改**：
   - 所有默认密码
   - SECRET_KEY使用强随机字符串
   - 关闭不必要的端口映射

2. **启用HTTPS**：
   - 使用Nginx反向代理
   - 配置SSL证书（Let's Encrypt）

3. **网络隔离**：
   - 使用Docker网络隔离服务
   - 限制对外暴露的端口

4. **日志管理**：
   - 配置日志轮转
   - 监控异常访问

## 📊 性能优化

### 资源限制

在`docker-compose.yml`中添加资源限制：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```

### 数据库优化

```bash
# 调整MySQL配置
# 在docker-compose.yml中添加配置文件挂载
volumes:
  - ./mysql.cnf:/etc/mysql/conf.d/custom.cnf
```

## 🆘 支持

遇到问题？

1. 查看[常见问题](#故障排查)
2. 查看服务日志：`docker-compose logs -f`
3. 提交Issue到GitHub仓库

## 📝 更新日志

- **2025-01-29**: 初始Docker部署方案
  - 完整的11个服务编排
  - 支持LLaMA-Factory、SwanLab、Dify集成
  - 包含健康检查和自动重启

## 📄 许可证

本项目采用MIT许可证。
