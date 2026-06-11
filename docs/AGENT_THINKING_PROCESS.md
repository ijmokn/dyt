# Agent 思考过程获取方案

本文档介绍如何获取 Azure AI Agent 的思考过程（Reasoning/Thinking Process）。

## 📋 方案概述

Azure AI Agent 在处理请求时会产生多种事件，通过监听这些事件可以完整追踪 Agent 的思考过程。

## 🎯 可获取的信息类型

### 1. 工具调用过程（Tool Calls）
- **工具名称**：Agent 决定使用哪个工具
- **调用参数**：传递给工具的参数
- **执行结果**：工具返回的数据
- **调用原因**：为什么选择此工具

### 2. 推理步骤（Reasoning Steps）
- **步骤创建**：新推理步骤开始
- **步骤类型**：message_creation, tool_calls, etc.
- **步骤状态**：in_progress, completed, failed
- **步骤输出**：每个步骤的结果

### 3. 响应生成过程
- **文本增量**：实时生成的文本片段
- **引用标注**：文件引用、URL 引用
- **完成状态**：生成完成的标记

## 🔧 实现方案

### 方案 A：扩展现有流式响应（推荐）

**优点**：
- ✅ 无需额外 API 调用
- ✅ 实时获取，延迟最低
- ✅ 前端可选择性显示

**实现步骤**：

#### 1. 扩展 Schema 定义

在 `src/server/schemas/chat.py` 添加：

```python
class ThinkingStep(BaseModel):
    """Agent 思考步骤"""
    step_id: str = Field(..., description="步骤 ID")
    step_type: str = Field(..., description="步骤类型: tool_call, reasoning, message")
    status: str = Field(..., description="状态: in_progress, completed, failed")
    content: Optional[str] = Field(None, description="步骤内容")
    timestamp: str = Field(..., description="时间戳")

class ToolCall(BaseModel):
    """工具调用信息"""
    tool_name: str = Field(..., description="工具名称")
    arguments: dict = Field(default_factory=dict, description="调用参数")
    result: Optional[str] = Field(None, description="执行结果")
    duration_ms: Optional[int] = Field(None, description="执行耗时（毫秒）")

class ThinkingProcess(BaseModel):
    """完整思考过程"""
    steps: List[ThinkingStep] = Field(default_factory=list)
    tool_calls: List[ToolCall] = Field(default_factory=list)
    total_duration_ms: int = Field(..., description="总耗时")
```

#### 2. 更新 ChatService 捕获事件

在 `src/server/services/chat_service.py` 的 `stream_agent_response` 函数中添加事件处理：

```python
# 捕获更多事件类型
async for event in response:
    # 现有事件处理...
    
    # 新增：步骤创建事件
    elif event.type == "response.step.created":
        step_info = {
            "step_id": event.step.id,
            "step_type": event.step.type,
            "status": "in_progress",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        yield f"data: {json.dumps({'type': 'thinking_step', 'data': step_info})}\n\n"
    
    # 新增：步骤完成事件
    elif event.type == "response.step.completed":
        step_info = {
            "step_id": event.step.id,
            "step_type": event.step.type,
            "status": "completed",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        yield f"data: {json.dumps({'type': 'thinking_step_completed', 'data': step_info})}\n\n"
    
    # 新增：工具调用开始
    elif event.type == "response.function_call_arguments.delta":
        # 流式接收工具调用参数
        yield f"data: {json.dumps({'type': 'tool_call_delta', 'data': event.delta})}\n\n"
    
    # 新增：工具调用完成
    elif event.type == "response.function_call_arguments.done":
        tool_call_info = {
            "call_id": event.call_id,
            "tool_name": event.name,
            "arguments": event.arguments,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        yield f"data: {json.dumps({'type': 'tool_call_complete', 'data': tool_call_info})}\n\n"
    
    # 新增：工具执行结果
    elif event.type == "response.function_call_output.done":
        tool_result_info = {
            "call_id": event.call_id,
            "output": event.output,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        yield f"data: {json.dumps({'type': 'tool_call_result', 'data': tool_result_info})}\n\n"
```

#### 3. 前端接收和显示

在 `src/widget/src/ChatWidget.tsx` 中处理新事件：

```typescript
// 解析 SSE 事件
const eventData = JSON.parse(data);

switch (eventData.type) {
  case 'thinking_step':
    // 显示思考步骤
    addThinkingStep(eventData.data);
    break;
    
  case 'tool_call_complete':
    // 显示工具调用
    addToolCall(eventData.data);
    break;
    
  case 'tool_call_result':
    // 显示工具执行结果
    updateToolCallResult(eventData.data);
    break;
    
  // ... 其他事件
}
```

#### 4. 数据库持久化（可选）

如果需要保存思考过程，扩展 Message 模型：

```python
# 在 src/server/models/__init__.py
class Message(Base):
    # 现有字段...
    
    # 新增：思考过程 JSON
    thinking_process = Column(JSONB, nullable=True, comment="Agent thinking process")
```

然后在保存消息时包含思考过程：

```python
assistant_msg = DBMessage(
    conversation_id=conversation.id,
    role="assistant",
    content=assistant_message,
    annotations=assistant_annotations,
    thinking_process={
        "steps": collected_steps,
        "tool_calls": collected_tool_calls,
        "duration_ms": total_duration
    },
    created_at=now,
    updated_at=now
)
```

---

### 方案 B：使用 OpenTelemetry 追踪

**优点**：
- ✅ 标准化的可观测性方案
- ✅ 可集成到 Azure Monitor
- ✅ 支持分布式追踪

**实现要点**：

```python
from opentelemetry import trace

tracer = trace.get_tracer(__name__)

with tracer.start_as_current_span("agent_thinking") as span:
    span.set_attribute("agent.id", agent.id)
    span.set_attribute("conversation.id", conversation.id)
    
    # 记录每个思考步骤
    with tracer.start_span("thinking_step") as step_span:
        step_span.set_attribute("step.type", "tool_call")
        step_span.set_attribute("tool.name", tool_name)
        # ... 执行步骤
```

查看追踪数据：
- Azure Monitor -> Application Insights -> 事务搜索
- Jaeger UI（如果本地部署）

---

### 方案 C：API 查询历史思考过程

**优点**：
- ✅ 不影响实时性能
- ✅ 可按需查询
- ✅ 支持复杂分析

**实现**：

添加新的 API 端点：

```python
@router.get(
    "/history/{conversation_id}/thinking",
    response_model=ThinkingProcessResponse,
    summary="获取会话的思考过程",
)
async def get_thinking_process(
    conversation_id: str,
    message_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取指定消息或整个会话的思考过程"""
    
    if message_id:
        # 查询特定消息的思考过程
        message = db.query(Message).filter(
            Message.id == message_id,
            Message.conversation_id == conversation_id
        ).first()
        
        if not message or not message.thinking_process:
            raise HTTPException(404, "Thinking process not found")
        
        return message.thinking_process
    else:
        # 查询整个会话的所有思考过程
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id,
            Message.thinking_process.isnot(None)
        ).all()
        
        return {
            "conversation_id": conversation_id,
            "messages": [
                {
                    "message_id": msg.id,
                    "thinking_process": msg.thinking_process
                }
                for msg in messages
            ]
        }
```

---

## 📊 UI 展示方案

### 选项 1：折叠面板
```
用户：你好
助手：你好！我可以帮你... 
  [▶ 查看思考过程]
```

点击后展开：
```
📝 思考过程：
  1. [09:30:01] 理解用户意图
  2. [09:30:02] 🔧 调用工具: search_knowledge_base
     参数: {"query": "greeting"}
     结果: "找到 3 条相关内容"
  3. [09:30:03] 生成响应
```

### 选项 2：侧边栏
```
┌─────────────────┬──────────────────┐
│  对话区域       │  思考过程面板    │
│                 │  ⚙️ 步骤 1       │
│  用户: ...      │  🔧 工具调用     │
│  助手: ...      │  📝 推理中...    │
└─────────────────┴──────────────────┘
```

### 选项 3：时间线视图
```
09:30:00 ━━━━●━━━━ 用户消息
09:30:01    ┗━ 🤔 分析意图
09:30:02       ┗━ 🔧 调用工具
09:30:03          ┗━ 💬 生成回复
```

---

## 🚀 快速开始

### 最小实现（10 分钟）

1. 修改 `chat_service.py` 添加两个事件捕获：
   ```python
   elif event.type == "response.step.created":
       yield f"data: {json.dumps({'type': 'step', 'step_type': event.step.type})}\n\n"
   ```

2. 前端添加简单日志：
   ```typescript
   if (eventData.type === 'step') {
       console.log('🤔 Agent 步骤:', eventData.step_type);
   }
   ```

3. 测试：打开浏览器控制台，发送消息，查看日志

---

## 📝 建议

**优先级排序：**
1. 🥇 **方案 A**（流式捕获） - 用户体验最好
2. 🥈 **方案 B**（OpenTelemetry） - 可观测性最强
3. 🥉 **方案 C**（API 查询） - 最灵活但延迟高

**分阶段实施：**
- **Phase 1**：先实现基本的步骤追踪（step.created, step.completed）
- **Phase 2**：添加工具调用详情
- **Phase 3**：添加数据库持久化
- **Phase 4**：完善 UI 展示

---

## ❓ 常见问题

**Q: 会影响性能吗？**
A: 流式事件本身就存在，只是增加了发送到前端的数据量，影响极小（约增加 10-20% 传输数据）。

**Q: 用户会看到所有思考过程吗？**
A: 可以在前端控制显示/隐藏，或者提供"开发者模式"开关。

**Q: 思考过程会被保存吗？**
A: 看需求。如果需要审计或调试，建议保存；否则只实时展示即可。

**Q: 支持哪些 Agent 类型？**
A: Azure AI Foundry 的所有 Agent 都支持这些事件。

---

## 🔗 相关文档

- [Azure AI Agent API 文档](https://learn.microsoft.com/azure/ai-services/agents/)
- [OpenTelemetry Python](https://opentelemetry.io/docs/instrumentation/python/)
- [Server-Sent Events 规范](https://html.spec.whatwg.org/multipage/server-sent-events.html)
