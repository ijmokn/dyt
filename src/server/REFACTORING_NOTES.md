# 项目重构说明

## 🎉 重构完成

本次重构按照企业级 FastAPI 项目标准对 `server/` 目录进行了全面改造。

---

## 📁 新的项目结构

```
src/server/
├── core/                          # 核心配置和基础设施
│   ├── __init__.py
│   ├── config.py                  # 统一配置管理 (Pydantic Settings)
│   ├── exceptions.py              # 自定义异常类
│   ├── exception_handlers.py     # 异常处理器
│   └── security.py                # 安全认证
│
├── schemas/                       # Pydantic 数据模型
│   ├── __init__.py
│   ├── chat.py                    # 聊天相关模型
│   ├── agent.py                   # Agent 相关模型
│   └── health.py                  # 健康检查模型
│
├── services/                      # 业务逻辑层
│   ├── __init__.py
│   ├── chat_service.py            # 聊天服务
│   └── agent_service.py           # Agent 服务
│
├── api/                           # API 层
│   ├── __init__.py
│   ├── main.py                    # FastAPI 应用工厂
│   ├── dependencies.py            # 依赖注入
│   └── routes/                    # 路由模块
│       ├── __init__.py
│       ├── health.py              # 健康检查路由
│       ├── agent.py               # Agent 信息路由
│       └── chat.py                # 聊天路由
│
├── util.py                        # 工具函数
├── logging_config.py              # 日志配置
└── requirements.txt               # 依赖包
```

---

## ✨ 主要改进

### 1. **分层架构**
- **core/** - 核心配置、异常、安全
- **schemas/** - 数据验证模型
- **services/** - 业务逻辑
- **api/** - API 路由和依赖注入

### 2. **Pydantic 数据验证**
- ✅ `ChatRequest` - 聊天请求验证
- ✅ `ChatMessage` - 消息格式验证
- ✅ `AgentResponse` - Agent 响应模型
- ✅ 自动 API 文档生成

### 3. **统一配置管理**
```python
from core.config import get_settings

settings = get_settings()
# 自动从环境变量加载
# 支持 .env 文件
# 类型安全
```

### 4. **自定义异常处理**
```python
from core.exceptions import ConversationError, AgentNotFoundError

raise ConversationError("Invalid conversation")
# 自动返回结构化 JSON 错误响应
```

### 5. **依赖注入重构**
```python
from api.dependencies import get_project_client, get_agent_version_details

@router.get("/agent")
async def get_agent(
    agent: AgentVersionDetails = Depends(get_agent_version_details)
):
    ...
```

### 6. **服务层抽象**
```python
from services.chat_service import ChatService

# 业务逻辑集中管理
messages = await ChatService.get_conversation_history(...)
```

---

## 🔧 如何使用

### 安装新依赖
```bash
pip install -r requirements.txt
```

### 启动应用
```bash
# 开发模式
uvicorn api.main:create_app --factory --reload

# 生产模式
gunicorn api.main:create_app --factory
```

### 访问 API 文档
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## 📊 对比：旧 vs 新

| 方面 | 旧代码 | 新代码 |
|------|--------|--------|
| **数据验证** | 手动解析 JSON | Pydantic 自动验证 |
| **配置管理** | 散落的 os.getenv() | 集中的 Settings 类 |
| **异常处理** | 只有全局 handler | 分层自定义异常 |
| **业务逻辑** | 混在路由中 (200+ 行) | 提取到服务层 |
| **依赖注入** | 零散的 Depends | 统一管理 |
| **项目结构** | 扁平化 | 清晰的分层架构 |
| **API 文档** | 基础自动生成 | 详细带示例 |

---

## 🚀 未来可扩展

现在的架构支持轻松添加：

1. **JWT 认证** - 在 `core/security.py` 中实现
2. **限流中间件** - 在 `api/main.py` 中添加
3. **缓存层** - 在 `services/` 中集成 Redis
4. **后台任务** - 使用 FastAPI BackgroundTasks
5. **单元测试** - 按层测试，依赖注入便于 mock
6. **监控指标** - 添加 Prometheus metrics

---

## ⚠️ 注意事项

### 旧代码保留
原有的 `api/routes.py` 和旧 `api/main.py` 的代码逻辑已完整迁移到新架构，但文件本身未删除。
如果测试无问题，可以删除：
- `api/routes.py` (已被 `api/routes/` 目录替代)

### 环境变量验证
新的配置系统会在启动时验证必需的环境变量，如果缺失会报错。

### 向后兼容
API 端点路径保持不变：
- `GET /` - 根路由
- `GET /health` - 新增健康检查
- `GET /agent` - Agent 信息
- `POST /chat` - 发送消息
- `GET /chat/history` - 获取历史

---

## 📝 迁移检查清单

- [x] 创建分层目录结构
- [x] 定义 Pydantic schemas
- [x] 实现统一配置管理
- [x] 创建自定义异常
- [x] 提取业务逻辑到服务层
- [x] 重构依赖注入
- [x] 重构路由
- [x] 更新 main.py
- [x] 更新 requirements.txt
- [ ] 测试所有 API 端点
- [ ] 删除旧代码文件

---

## 🐛 故障排查

如果遇到问题：

1. **ModuleNotFoundError** - 运行 `pip install -r requirements.txt`
2. **配置错误** - 检查环境变量是否设置
3. **导入错误** - 确保从项目根目录运行

---

**重构完成！代码现在更清晰、可维护、可扩展。** 🎊
