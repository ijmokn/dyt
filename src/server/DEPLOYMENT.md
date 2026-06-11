# 🚀 后端部署指南

## 📋 前置要求

### 1. Azure 资源
- ✅ Azure AI Project (已创建)
- ✅ Azure AI Agent (已部署)
- ✅ PostgreSQL 数据库 (Azure Database for PostgreSQL 或自建)

### 2. 环境变量配置

复制环境变量模板：
```bash
cp .env.example .env
```

编辑 `.env` 文件，填写以下必需字段：

| 变量名 | 说明 | 示例 |
|--------|------|------|
| `AZURE_EXISTING_AIPROJECT_ENDPOINT` | Azure AI Project 端点 | `https://xxx.cognitiveservices.azure.com/` |
| `AZURE_EXISTING_AIPROJECT_RESOURCE_ID` | 资源 ID | `/subscriptions/.../accounts/xxx` |
| `AZURE_EXISTING_AGENT_ID` | Agent ID（格式：名称:版本） | `my-agent:v1` |
| `DATABASE_URL` | PostgreSQL 连接字符串 | `postgresql://user:pass@host:5432/db` |

---

## 🐳 Docker 部署

### 方法 1：使用 Docker Compose（推荐）

创建 `docker-compose.yml`：

```yaml
version: '3.8'

services:
  backend:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "50505:50505"
    environment:
      - AZURE_EXISTING_AIPROJECT_ENDPOINT=${AZURE_EXISTING_AIPROJECT_ENDPOINT}
      - AZURE_EXISTING_AIPROJECT_RESOURCE_ID=${AZURE_EXISTING_AIPROJECT_RESOURCE_ID}
      - AZURE_EXISTING_AGENT_ID=${AZURE_EXISTING_AGENT_ID}
      - DATABASE_URL=${DATABASE_URL}
      - RUNNING_IN_PRODUCTION=true
      - CORS_ALLOWED_ORIGINS=https://your-frontend.com
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:50505/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
```

启动服务：
```bash
docker-compose up -d
```

查看日志：
```bash
docker-compose logs -f backend
```

### 方法 2：直接使用 Docker

构建镜像：
```bash
docker build -t ai-agent-backend:latest .
```

运行容器：
```bash
docker run -d \
  --name ai-agent-backend \
  -p 50505:50505 \
  --env-file .env \
  -e RUNNING_IN_PRODUCTION=true \
  ai-agent-backend:latest
```

---

## ☁️ Azure 部署

### 部署到 Azure Container Apps

1. **创建容器注册表**：
```bash
az acr create \
  --resource-group <resource-group> \
  --name <registry-name> \
  --sku Basic
```

2. **构建并推送镜像**：
```bash
az acr build \
  --registry <registry-name> \
  --image ai-agent-backend:latest \
  --file Dockerfile .
```

3. **创建 Container App**：
```bash
az containerapp create \
  --name ai-agent-backend \
  --resource-group <resource-group> \
  --environment <environment-name> \
  --image <registry-name>.azurecr.io/ai-agent-backend:latest \
  --target-port 50505 \
  --ingress external \
  --env-vars \
    AZURE_EXISTING_AIPROJECT_ENDPOINT="<endpoint>" \
    AZURE_EXISTING_AGENT_ID="<agent-id>" \
    DATABASE_URL="<db-url>" \
    RUNNING_IN_PRODUCTION=true
```

### 部署到 Azure App Service

```bash
az webapp create \
  --resource-group <resource-group> \
  --plan <app-service-plan> \
  --name <app-name> \
  --deployment-container-image-name <registry>.azurecr.io/ai-agent-backend:latest

az webapp config appsettings set \
  --resource-group <resource-group> \
  --name <app-name> \
  --settings \
    AZURE_EXISTING_AIPROJECT_ENDPOINT="<endpoint>" \
    DATABASE_URL="<db-url>"
```

---

## 🔐 Azure 身份认证

Dockerfile 已配置为使用 **DefaultAzureCredential**，支持以下认证方式（按优先级）：

1. ✅ **环境变量**（推荐生产环境）：
```bash
AZURE_TENANT_ID=xxx
AZURE_CLIENT_ID=xxx
AZURE_CLIENT_SECRET=xxx
```

2. ✅ **Managed Identity**（推荐 Azure 服务）：
   - Container Apps / App Service 自动配置

3. ✅ **Azure CLI**（本地开发）：
```bash
az login
```

---

## 📊 数据库初始化

运行 SQL 脚本创建表：

```bash
psql $DATABASE_URL < ../../scripts/chat_history_schema_postgres.sql
```

或使用 PostgreSQL 客户端手动执行 `scripts/chat_history_schema_postgres.sql`。

---

## ✅ 健康检查

部署后验证服务状态：

```bash
# 健康检查
curl http://localhost:50505/health

# 预期响应
{
  "status": "healthy",
  "version": "1.0.0",
  "agent": {
    "id": "agent_name:version",
    "name": "agent_name"
  }
}
```

---

## 🔧 常见问题

### 1. 容器启动失败

**查看日志**：
```bash
docker logs ai-agent-backend
```

**常见原因**：
- ❌ 环境变量未设置
- ❌ 数据库连接失败
- ❌ Azure 认证失败

### 2. Azure 认证错误

确保容器有访问 Azure 资源的权限：
- Managed Identity 已启用并授予 **Cognitive Services User** 角色
- 或提供正确的 Service Principal 凭据

### 3. 数据库连接超时

检查：
- PostgreSQL 服务是否运行
- 网络安全组/防火墙规则
- 连接字符串格式是否正确

---

## 📝 日志查看

**Docker**：
```bash
docker logs -f ai-agent-backend
```

**Azure Container Apps**：
```bash
az containerapp logs show \
  --name ai-agent-backend \
  --resource-group <resource-group> \
  --follow
```

**Azure App Service**：
```bash
az webapp log tail \
  --name <app-name> \
  --resource-group <resource-group>
```

---

## 🔄 更新部署

### Docker Compose
```bash
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Azure Container Apps
```bash
az containerapp update \
  --name ai-agent-backend \
  --resource-group <resource-group> \
  --image <registry>.azurecr.io/ai-agent-backend:latest
```

---

## 📈 性能优化

1. **Worker 数量调整**（`gunicorn.conf.py`）：
```python
workers = (cpu_count * 2) + 1  # 当前配置
```

2. **启用连接池**（PostgreSQL）：
```python
# 在 DATABASE_URL 添加参数
DATABASE_URL=postgresql://...?pool_size=10&max_overflow=20
```

3. **启用 Azure Monitor**：
```bash
ENABLE_AZURE_MONITOR_TRACING=true
```

---

## 🛡️ 安全建议

✅ **已实现**：
- 非 root 用户运行（UID 1000）
- 健康检查配置
- 环境变量管理
- CORS 限制

⚠️ **建议增强**：
- 使用 Azure Key Vault 存储敏感信息
- 配置 HTTPS/TLS 证书
- 启用 Azure Monitor 告警
- 定期更新依赖包
