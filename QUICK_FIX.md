# 快速修复指南

## 问题解决

你遇到的 `ImportError: cannot import name 'get_db'` 错误已经修复。

## 修复内容

1. ✅ **添加了 `get_db` 函数** 到 `app/database.py`
2. ✅ **修复了 `main.py` 中的导入问题**
3. ✅ **添加了缺失的 `__init__.py` 文件**
4. ✅ **创建了调试启动脚本**
5. ✅ **修复了前端 Sidebar 组件**

## 启动方法

### 方法1：使用调试脚本（推荐）
```bash
cd modeltrain
python debug_start.py
```

### 方法2：传统启动
```bash
cd modeltrain/backend
python main.py
```

### 方法3：使用uvicorn
```bash
cd modeltrain/backend
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

## 启动前端

另开一个终端：
```bash
cd modeltrain/frontend
npm install
npm run dev
```

## 访问地址

- **前端**: http://localhost:5173
- **后端API**: http://localhost:8000
- **API文档**: http://localhost:8000/docs

## 如果还有问题

1. 检查Python版本 (需要3.8+)
2. 检查是否在正确的目录
3. 查看终端输出的详细错误信息
4. 确保安装了所有依赖：
   ```bash
   cd modeltrain/backend
   pip install -r requirements.txt
   ```

## 功能测试

启动成功后可以测试：

1. **模型配置**: 访问 `/model-config` 页面
2. **模型测试**: 访问 `/model-test` 页面
3. **API文档**: 访问 `http://localhost:8000/docs`

## 默认账号

- 管理员: admin / admin
- 可以注册新用户

---

📝 **提示**: 如果 `debug_start.py` 显示所有导入都成功，说明修复生效了！ 