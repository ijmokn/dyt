# JMate 桌面智能 Agent

JMate 是一个基于 Python、PySide6、Microsoft Agent Framework 和 Azure AI Foundry 的 Windows 桌面智能 Agent。程序在同一进程内连接桌面界面与 Python 后端，由 Hub Agent 统一处理普通问答、公司制度查询和本地文件型 Skill。


## 项目结构

以下只列源码和构建配置；`.venv/`、`build/`、`dist/`、`dist_upx/`、`installer_output/`、`logs/` 等依赖或产物目录不参与源码说明。

```text
dyt/
├─ main.py                         # 统一启动入口及 PyInstaller DLL/路径适配
├─ frontend/
│  ├─ main.py                      # QApplication、日志、主题、Hub Agent 后台初始化
│  ├─ app/                         # 主窗口、全局状态、主题及常量
│  ├─ views/chat_view.py           # 聊天消息区及发送流程
│  ├─ widgets/                     # 登录、设置、标题栏、输入栏、用户卡片等控件
│  ├─ services/                    # Chat/Auth 服务及唯一后端边界 BackendClient
│  ├─ workers/task.py              # Qt 线程池任务封装
│  └─ resources/                   # QSS 和 SVG
├─ backend/
│  ├─ services/hub_agent.py        # Hub Agent 初始化、队列、会话及同步调用入口
│  ├─ services/azure_agent.py      # 可选的直连 Foundry Agent 方案（当前未挂载）
│  ├─ services/auth_service.py     # 8 位社员号校验
│  ├─ services/agent_config.py     # Azure/Foundry 环境配置加载
│  ├─ services/attendance_config.py# 用户业务配置读写
│  ├─ services/crypto_service.py   # 配置密码的 Fernet 加密与解密
│  ├─ services/skill_script_runner.py # 文件型 Skill 子进程执行器
│  └─ skills/attendance-export/    # 考勤 PDF 导出 Skill
├─ shared/
│  ├─ protocol.py                  # 前后端共享请求/响应对象
│  └─ skill_catalog.py             # UI 技能目录
├─ JMate.spec                      # PyInstaller onedir 配置，与安装器目录一致
├─ JMateInstaller.iss              # Inno Setup 安装器脚本（当前收集 onedir）
├─ azure.env                       # 本地 Azure 配置
├─ attendance-config.json          # 当前仓库中的业务配置文件（见下方文件名注意事项）
└─ installer/                      # 安装器附带文件（当前为 Node.js MSI）
```

## 前端界面


### 设置界面

设置窗口包含：

- 个人信息：禀议、PJCOST、考勤账号/密码以及导出目录；
- 界面主题和字体大小；
- Enter 发送行为；
- UI 技能项的启用状态；
- 退出登录与未保存修改确认。

账号配置写入 `%USERPROFILE%\.attendance-config.json`。当前 `ENCRYPT_PASSWORD_ON_SAVE = False`，密码以明文保存。

## 前后端连接和调用方式

### 聊天调用链

```text
ChatView._handle_send()
  → ChatService.get_reply_async()          # QThreadPool，避免阻塞窗口
  → ChatRequest                            # shared/protocol.py
  → BackendClient.send_chat()
  → _LocalBackendAdapter.send_chat()
  → HubAgent.reply()
  → 后台请求队列 + 独立 asyncio event loop
  → Agent Framework Hub Agent
      ├─ 普通问答：FoundryChatClient
      ├─ 公司制度：FoundryAgent.as_tool(query_company_rules)
      └─ 操作任务：SkillsProvider + 本地文件型 Skill
  → ChatResponse
  → Qt signal/callback
  → ChatView 更新消息气泡
```

`frontend/services/backend_client.py` 是前端访问后端的唯一边界。对外方法为：

```python
BackendClient.send_chat(request: ChatRequest) -> ChatResponse
BackendClient.login(request: LoginRequest) -> LoginResponse
```

如果将来改成 HTTP、WebSocket 或 Node.js 子进程，只需实现相同的 adapter 方法并注入 `BackendClient`，不要让 Qt 页面直接依赖传输层。

### 登录调用链

```text
LoginDialog
  → AuthService.login()
  → LoginRequest(provider=MOCK)
  → BackendClient.login()
  → BackendAuthService.login()
  → LoginResponse
  → build_login_config() + save_config()
  → AppState 更新登录状态和用户名
```

### Hub Agent 运行方式

`frontend/main.py` 启动 `start_initialize_hub_agent_async()`。后端线程创建独立的 asyncio event loop、Azure 凭据、Foundry 客户端、托管 Agent 工具和本地 `SkillsProvider`，并创建一个长期会话。桌面聊天线程把请求放入队列，Hub 线程串行消费并把结果写入 `Future`。


### 文件型 Skill

Hub Agent 扫描 `backend/skills/`。`skill_script_runner.py` 使用子进程运行 Skill 脚本：

- 源码环境：使用当前虚拟环境 Python；
- 打包环境：默认寻找安装目录下 `runtime/python/python.exe`；
- 可用 `JMATE_SKILL_PYTHON` 环境变量覆盖解释器路径。

当前考勤导出脚本还需要 Python Playwright 及 Chromium。仅打包 `JMate.exe` 并不会自动提供私有 Python、Playwright 或浏览器，因此发布前必须把这些运行时放入安装目录，或者为 `JMATE_SKILL_PYTHON` 指定已安装依赖的 Python。

## 配置

### Azure/Foundry

复制 `azure.dev.example` 为开发配置，或在项目根目录/EXE 目录准备 `.env` 或 `azure.env`：

```dotenv
FOUNDRY_PROJECT_ENDPOINT=
FOUNDRY_MODEL=
FOUNDRY_AGENT_NAME=
FOUNDRY_AGENT_VERSION=
AZURE_CLIENT_ID=
AZURE_TENANT_ID=
AZURE_CLIENT_SECRET=
```

加载顺序为运行目录 `.env`、运行目录 `azure.env`、应用目录 `.env`、应用目录 `azure.env`，且不会覆盖系统环境变量。


## 开发运行

建议使用 Python 3.12 及虚拟环境：

```powershell
cd D:\code\dyt
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -r frontend\requirements.txt
python -m pip install pyinstaller python-dotenv cryptography playwright agent-framework agent-framework-foundry agent-framework-openai
playwright install chromium
python main.py
```

`frontend/requirements.txt` 目前只列出 PySide6 和部分 Azure 包，上述附加依赖来自当前源码导入和打包配置。



## 打包为 Windows 程序

项目提供两种打包入口：推荐使用 `JMate.spec` 进行当前完整构建；如需直接使用 PyInstaller 命令行，也可参考 `scripts/package_commands.md` 中记录的无 UPX onedir、UPX onedir 和 UPX onefile 三套命令。

### 方法一：使用 JMate.spec（推荐）

`JMate.spec` 已配置为 onedir（文件中加了注释），输出的 `JMate` 目录可由 `JMateInstaller.iss` 整体收集。由于 `.spec` 文件不能固定命令行的 `distpath`，构建时必须显式指定 `--distpath dist_upx`：

```powershell
cd D:\code\dyt
Remove-Item build,dist_upx -Recurse -Force -ErrorAction SilentlyContinue
pyinstaller --clean --noconfirm --distpath dist_upx JMate.spec
```

生成结果应为 `dist_upx\JMate\JMate.exe` 以及同目录下的 `_internal` 和相关依赖。先直接运行该 EXE 做冒烟测试，再制作安装器。spec 当前启用 UPX，并排除了 Python、Qt、Shiboken 和 VC Runtime DLL；如发布环境出现 DLL 加载问题，可将 `EXE` 和 `COLLECT` 中的 `upx` 改为 `False`，稳定性通常优先于体积。

### 方法二：使用 scripts/package_commands.md 中的命令

不使用 spec 时，可直接执行 [`scripts/package_commands.md`](scripts/package_commands.md) 中保存的 PyInstaller 命令：

- **稳定版（无 UPX）**：使用 `--noupx --onedir`，默认输出到 `dist\JMate\`；
- **UPX 测试版**：使用 `--onedir --distpath dist_upx`，输出到 `dist_upx\JMate\`，可直接交给当前 `.iss`；
- **UPX onefile 版**：使用 `--onefile --distpath dist_upx_onefile`，生成单个 EXE，不符合当前 `.iss` 的 onedir 收集路径。


## 使用 Inno Setup 制作安装程序

1. 安装 Inno Setup 6.7.3。
2. 完成 onedir 打包并确认 `dist_upx\JMate\JMate.exe` 可运行。
3. 确认 `installer\node-v24.16.0-x64.msi` 存在；如更新 MSI，同时修改 `.iss` 中的文件名与版本常量。
4. 在项目根目录运行：

```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" JMateInstaller.iss
```

5. 产物位于 `installer_output\JMateSetup.exe`。

`.iss` 的主要流程是：（iss文件加了代码注释）

```text
[Setup]  定义应用、版本、安装目录、压缩、架构与管理员权限
[Files]  复制 JMate onedir 文件，并把 Node MSI 嵌入安装器临时资源
[Icons]  创建开始菜单和公共桌面快捷方式
[Run]    安装结束后可选启动 JMate
[Code]   从注册表查找 node.exe → 读取版本 → 必要时静默安装内置 MSI
```

注意：当前 Python Skill 使用 Playwright Python，不直接依赖 Node.js；保留 Node.js 安装检查意味着项目还有其他 Node 运行时需求。如果没有这类需求，可在确认后移除 Node MSI 和 `[Code]` 检测逻辑，以减小安装包体积并避免不必要的管理员安装。
