# 防腐层（Anti-Corruption Layer）重构完成

## 📊 重构概览

成功实施防腐层架构，将业务代码与 Azure SDK 解耦，提升代码的可维护性、可测试性和可扩展性。

## 🎯 重构目标

✅ **解耦外部依赖**：业务代码不再直接依赖 Azure SDK  
✅ **提升可测试性**：通过接口 Mock 简化单元测试  
✅ **增强可扩展性**：支持多云平台切换（Azure、OpenAI、本地模型）  
✅ **改善可维护性**：SDK 升级只影响适配器层  

---

## 📁 新增文件结构

```
src/server/
├── adapters/                           # 防腐层（新增）
│   ├── __init__.py                     # 导出接口和模型
│   ├── interfaces.py                   # 抽象接口定义
│   ├── models.py                       # 领域模型定义
│   └── azure/                          # Azure 实现
│       ├── __init__.py
│       ├── azure_agent_service.py      # Azure 服务实现
│       └── azure_models_mapper.py      # Azure 模型转换器
│
├── api/
│   ├── dependencies.py                 # ✅ 新增防腐层依赖注入
│   ├── main.py                         # ✅ 使用防腐层初始化
│   └── routes/
│       └── chat.py                     # ✅ 使用防腐层接口
│
└── services/
    └── chat_service.py                 # ✅ 使用防腐层接口
```

---

## 🔧 核心组件

### 1. 领域模型 (`adapters/models.py`)

定义业务代码使用的数据结构，与外部 SDK 解耦：

```python
@dataclass
class StreamEvent:
    """流式响应事件（业务模型）"""
    event_type: StreamEventType  # "text_delta" | "completed"
    content: Optional[str] = None
    delta: Optional[str] = None
    annotations: Optional[List[Dict[str, Any]]] = None

@dataclass
class AgentInfo:
    """Agent 信息（业务模型）"""
    id: str
    name: str
    version: str
    description: Optional[str] = None
```

### 2. 抽象接口 (`adapters/interfaces.py`)

定义业务层需要的能力，具体实现由适配器提供：

```python
class IAIAgentService(ABC):
    """AI Agent 服务抽象接口"""
    
    @abstractmethod
    async def stream_chat(...) -> AsyncGenerator[StreamEvent, None]:
        """流式聊天"""
        pass
    
    @abstractmethod
    async def get_agent(...) -> AgentInfo:
        """获取 Agent 信息"""
        pass
```

### 3. Azure 适配器 (`adapters/azure/`)

#### `azure_agent_service.py` - Azure 实现
```python
class AzureAIAgentService(IAIAgentService):
    """Azure AI Projects 实现"""
    
    async def stream_chat(...):
        # 调用 Azure SDK
        async with self.client.get_openai_client() as openai_client:
            response = await openai_client.responses.create(...)
            
            # 转换 Azure 事件为领域事件
            async for azure_event in response:
                domain_event = self._mapper.map_stream_event(azure_event)
                yield domain_event
```

#### `azure_models_mapper.py` - 模型转换器
```python
class AzureModelsMapper:
    """Azure SDK → 领域模型转换"""
    
    def map_stream_event(self, azure_event) -> StreamEvent:
        # Azure: "response.output_text.delta"
        if azure_event.type == "response.output_text.delta":
            # 转换为业务模型
            return StreamEvent(
                event_type=StreamEventType.TEXT_DELTA,
                delta=azure_event.delta
            )
```

---

## 🔄 重构对比

### 修改前 ❌

**main.py**
```python
from azure.ai.projects.aio import AIProjectClient
from azure.identity.aio import DefaultAzureCredential

# 直接创建 Azure 客户端
credential = DefaultAzureCredential()
project_client = AIProjectClient(endpoint=..., credential=credential)
app.state.ai_project = project_client
```

**chat.py**
```python
from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import AgentVersionDetails

async def chat(
    project_client: AIProjectClient = Depends(get_project_client),
    agent: AgentVersionDetails = Depends(get_agent_version_details)
):
    # 路由层直接依赖 Azure SDK
```

**chat_service.py**
```python
async def stream_agent_response(
    agent: AgentVersionDetails,
    project_client: AIProjectClient,
    ...
):
    async with project_client.get_openai_client() as openai_client:
        # 业务代码直接调用 Azure SDK
        response = await openai_client.responses.create(...)
        async for event in response:
            if event.type == "response.output_text.delta":  # Azure 特定
                assistant_message += event.delta
```

### 修改后 ✅

**main.py**
```python
from adapters.interfaces import IAIAgentService
from adapters.azure import AzureAIAgentService

# 创建防腐层服务
agent_service: IAIAgentService = AzureAIAgentService(endpoint=...)
app.state.agent_service = agent_service  # 存储接口
```

**chat.py**
```python
from adapters.interfaces import IAIAgentService
from adapters.models import AgentInfo

async def chat(
    agent_service: IAIAgentService = Depends(get_agent_service),
    agent: AgentInfo = Depends(get_agent_info)
):
    # 路由层依赖抽象接口
```

**chat_service.py**
```python
async def stream_agent_response(
    agent: AgentInfo,
    agent_service: IAIAgentService,
    ...
):
    # 通过防腐层调用
    async for event in agent_service.stream_chat(...):
        if event.event_type == StreamEventType.TEXT_DELTA:  # 业务模型
            assistant_message += event.delta
```

---

## ✨ 收益分析

### 1. 可测试性提升

**重构前：**
```python
# 必须 Mock 复杂的 Azure SDK
mock_client = MagicMock(spec=AIProjectClient)
mock_openai = MagicMock()
mock_client.get_openai_client.return_value.__aenter__.return_value = mock_openai
# ... 更多 Mock 代码
```

**重构后：**
```python
# 只需 Mock 简单的接口
mock_service = Mock(spec=IAIAgentService)
mock_service.stream_chat = AsyncMock(return_value=[
    StreamEvent(event_type=StreamEventType.TEXT_DELTA, delta="Hello")
])
```

### 2. 平台切换能力

**添加 OpenAI 支持：**
```python
# 1. 创建 OpenAI 适配器（新增文件）
class OpenAIAgentService(IAIAgentService):
    async def stream_chat(...):
        # 调用 OpenAI SDK
        client = OpenAI(api_key=self.api_key)
        stream = client.chat.completions.create(...)
        
        # 转换为业务模型
        for chunk in stream:
            yield StreamEvent(...)

# 2. 修改配置（main.py，一行代码）
if settings.AI_PROVIDER == "openai":
    agent_service = OpenAIAgentService(...)

# ✅ 业务代码完全不需要改！
```

### 3. SDK 升级隔离

假设 Azure SDK 升级，事件名称改变：
```python
# 只需修改 azure_models_mapper.py
def map_stream_event(self, azure_event):
    if azure_event.type == "output.delta":  # 新名称
        return StreamEvent(
            event_type=StreamEventType.TEXT_DELTA,  # 业务名称不变
            delta=azure_event.delta
        )

# ✅ 业务代码完全不受影响
```

---

## 📈 影响范围

| 文件 | 修改类型 | 说明 |
|------|---------|------|
| `adapters/**` | 新增 | 防腐层实现 |
| `api/main.py` | 重构 | 使用防腐层初始化 |
| `api/dependencies.py` | 新增函数 | 防腐层依赖注入 |
| `api/routes/chat.py` | 重构 | 使用防腐层接口 |
| `services/chat_service.py` | 重构 | 使用防腐层接口 |

---

## 🚀 后续优化建议

### 1. 完全移除 OpenAI 对话管理

当前 `get_or_create_conversation` 还依赖 OpenAI SDK，可以进一步重构：

```python
# 方案 A：完全使用数据库管理对话
# 移除 OpenAI conversation API 调用

# 方案 B：将对话管理也纳入防腐层
class IAIAgentService:
    @abstractmethod
    async def create_conversation(...) -> str:
        pass
```

### 2. 异步保存消息

当前消息保存在 finally 块中同步执行，可以优化为异步：

```python
# 使用后台任务异步保存
asyncio.create_task(
    self._save_assistant_message_async(...)
)
```

### 3. 添加重试机制

在防腐层添加重试逻辑，提升稳定性：

```python
class AzureAIAgentService:
    @retry(max_attempts=3, backoff=exponential)
    async def stream_chat(...):
        # 调用 Azure SDK
```

---

## 🎓 架构原则总结

1. **依赖倒置原则（DIP）**
   - 业务层依赖抽象接口（IAIAgentService）
   - 基础设施层实现接口（AzureAIAgentService）

2. **单一职责原则（SRP）**
   - 适配器负责与外部系统交互
   - 转换器负责模型转换
   - 业务服务负责业务逻辑

3. **开闭原则（OCP）**
   - 对扩展开放：添加新平台只需新增适配器
   - 对修改关闭：业务代码无需修改

4. **接口隔离原则（ISP）**
   - 接口定义业务所需的最小能力集合
   - 不强迫实现者提供不需要的功能

---

## ✅ 验证清单

- [x] 防腐层目录结构创建完成
- [x] 领域模型定义完成（StreamEvent、AgentInfo 等）
- [x] 抽象接口定义完成（IAIAgentService）
- [x] Azure 适配器实现完成
- [x] Azure 模型转换器实现完成
- [x] 依赖注入配置更新完成
- [x] main.py 重构完成
- [x] chat.py 路由重构完成
- [x] chat_service.py 服务重构完成
- [ ] 单元测试覆盖（待补充）
- [ ] 集成测试验证（待执行）
- [ ] 性能测试（待执行）

---

## 📝 使用指南

### 启动应用

```bash
# 激活虚拟环境
.venv\Scripts\activate

# 进入服务器目录
cd src/server

# 启动服务
python -m uvicorn api.main:app --host 0.0.0.0 --port 50505
```

### 切换 AI 平台（未来）

```python
# config.py
AI_PROVIDER = "azure"  # 或 "openai" 或 "local"

# main.py
if settings.AI_PROVIDER == "azure":
    agent_service = AzureAIAgentService(...)
elif settings.AI_PROVIDER == "openai":
    agent_service = OpenAIAgentService(...)
```

---

**重构完成时间：** 2026年5月13日  
**架构模式：** 防腐层（Anti-Corruption Layer）  
**设计原则：** SOLID、依赖倒置、接口隔离
