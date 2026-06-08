# J-Mate 桌面智能助手

这是一个基于 Python + PySide6 的桌面前端项目，目前后端仍是本地 mock。
当前重构目标是让前端、后端、共享协议尽量解耦，方便后续接入真实 Agent、HTTP 服务、WebSocket、Node.js 运行时或第三方 API。

## 启动方式

推荐从项目根目录统一启动：

```powershell
cd D:\code\dyt
.\.venv\Scripts\python.exe main.py
```

旧入口仍然保留，便于只调试前端：

```powershell
cd D:\code\dyt
.\.venv\Scripts\python.exe frontend\main.py
```

安装前端依赖：

```powershell
cd D:\code\dyt
.\.venv\Scripts\python.exe -m pip install -r frontend\requirements.txt
```

当前 mock 登录演示账号：

```text
用户名：admin
密码：123456
```

输入其他用户名或密码会返回“用户名或密码不正确”，用于验证登录失败界面。

## 项目结构

```text
dyt/
├─ main.py                         # 统一启动入口，负责配置导入路径并启动前端
├─ frontend/                       # PySide6 桌面前端
│  ├─ main.py                      # 前端独立启动入口
│  ├─ app/
│  │  ├─ constants.py              # 前端展示文案常量
│  │  ├─ main_window.py            # 主窗口布局和全局交互
│  │  ├─ state.py                  # 前端运行时状态和 Qt 信号
│  │  ├─ theme.py                  # QSS 加载入口
│  │  └─ theme_tokens.py           # Python 动态样式使用的颜色和尺寸 token
│  ├─ services/
│  │  ├─ backend_client.py         # 前端访问后端的唯一客户端门面
│  │  ├─ chat_service.py           # 聊天服务，把 UI 输入转换成协议请求
│  │  └─ auth_service.py           # 登录服务，把登录输入转换成协议请求
│  ├─ views/                       # 页面级界面
│  ├─ widgets/                     # 可复用控件
│  ├─ workers/                     # Qt 后台任务封装
│  ├─ resources/                   # QSS、图标、图片等静态资源
│  └─ utils/                       # 前端工具函数
├─ backend/                        # 后端/Agent/mock 服务层
│  └─ services/
│     ├─ mock_agent.py             # 当前 mock Agent 入口
│     ├─ mock_reply_rules.py       # mock 回复规则
│     └─ auth_service.py           # 当前 mock 登录服务
├─ shared/                         # 前后端共享定义
│  ├─ protocol.py                  # Chat/Login 请求和响应协议对象
│  └─ skill_catalog.py             # 技能目录和技能 id 定义
└─ scripts/                        # 后续构建、打包、启动脚本
```

## 前端到后端的接口边界

前端页面和控件不要直接 import `backend.*`。

当前唯一允许直接接触后端实现的前端文件是：

```text
frontend/services/backend_client.py
```

它对上层只暴露两个方法：

```python
BackendClient.send_chat(request: ChatRequest) -> ChatResponse
BackendClient.login(request: LoginRequest) -> LoginResponse
```

上层调用关系：

```text
ChatView / LoginDialog
        ↓
frontend/services/chat_service.py
frontend/services/auth_service.py
        ↓
frontend/services/backend_client.py
        ↓
backend/services/*
```

这样做的目的：后续如果后端从本地 mock 改成 HTTP、WebSocket、stdio、Node.js 或真实 Agent，只需要替换 `BackendClient` 内部 adapter，不需要修改 PySide6 页面和控件。

## 共享协议

前后端通过 `shared/protocol.py` 中的数据对象通信。

### 聊天请求

```python
ChatRequest(
    text: str,
    active_skill_id: str | None = None,
    active_skill_name: str = "通用助手",
)
```

### 聊天响应

```python
ChatResponse(
    role: MessageRole,
    text: str,
)
```

### 登录请求

```python
LoginRequest(
    provider: LoginProvider,
    username: str = "",
    password: str = "",
)
```

### 登录响应

```python
LoginResponse(
    success: bool,
    user_id: str | None = None,
    user_name: str | None = None,
    access_token: str | None = None,
    message: str = "",
)
```

后端人员接入真实登录时，建议保持这个协议不变。Microsoft、企业 SSO、设备码、token 刷新等细节应放在后端服务里，不要写到 PySide6 控件中。

当前前端登录流程：

```text
LoginDialog 收集用户名/密码
        ↓
AuthService.login()
        ↓
BackendClient.login(LoginRequest)
        ↓
backend/services/auth_service.py
        ↓
LoginResponse
        ↓
成功时显示登录成功界面，失败时显示用户名/密码错误界面
```

## 技能目录

技能 id 和展示信息统一放在：

```text
shared/skill_catalog.py
```

当前默认技能：

```text
email     月末考勤
summary   休假申请
schedule  加班申请
report    考勤填写
```

前端使用这些技能渲染按钮和设置项；后端可以使用同一批 skill id 做 Agent 路由或工具选择。

## 后端接入建议

当前 `frontend/services/backend_client.py` 内部使用 `_LocalBackendAdapter` 调用本地 mock 后端。

如果后续接 HTTP，可以新增类似：

```python
class HttpBackendAdapter:
    def send_chat(self, request: ChatRequest) -> ChatResponse:
        ...

    def login(self, request: LoginRequest) -> LoginResponse:
        ...
```

如果后续接 Node.js 或 Agent runtime，也建议实现同样的方法签名，然后注入给 `BackendClient`。

前端原则：

- 页面和控件只处理展示、输入和状态刷新。
- `ChatService/AuthService` 只负责把 UI 输入转换成 shared 协议对象。
- `BackendClient` 是前端访问后端的唯一边界。
- 真实业务逻辑、第三方 API、Agent 调用、token 管理放在后端。

## 验证命令

编译检查：

```powershell
cd D:\code\dyt
.\.venv\Scripts\python.exe -m compileall -q frontend backend shared main.py
```

聊天接口 smoke test：

```powershell
cd D:\code\dyt
.\.venv\Scripts\python.exe -c "import sys; sys.path.insert(0, r'D:\code\dyt\frontend'); sys.path.insert(0, r'D:\code\dyt'); from services.chat_service import ChatService; print(ChatService().get_reply('查询今天考勤', None, '通用助手'))"
```
