---
name: attendance-export
description: 当用户需要从 AdacoWeb 导出考勤表并保存 PDF 到指定目录时使用。支持配置文件自定义用户信息。
allowed-tools: Read Write Glob Grep Powershell
---

# 考勤表 PDF 导出

## 作用
自动打开 `http://adacodalian.ajis-group.com.cn/AdacoWeb/login`，登录后点击 `考勤管理` → 两次 `检索` → `打印报表`，将下载的 PDF 文件保存到指定目录。

## � 环境要求

需要安装 Playwright（Python）：

```bash
pip install playwright
playwright install chromium
```

## 🔧 配置（推荐）

**首次使用前请配置个人信息**，避免修改代码：

1. 创建配置文件：
   ```powershell
   notepad "$env:USERPROFILE\.attendance-config.json"
   ```

2. 填入以下内容：
   ```json
   {
     "attendance": {
       "username": "你的用户名",
       "password": "你的密码"
     },
     "common": {
       "outputDir": "D:\\report"
     }
   }
   ```

## 执行步骤
1. 运行 Python 脚本：
   ```
   python scripts/export-attendance.py [输出目录]
   ```
2. 脚本会自动：
   - 使用配置文件中的账号密码登录
   - 每一步等待 5~10 秒（慢加载页面）
   - 点击「考勤管理」进入考勤页面
   - 点击两次「检索」按钮刷新数据
   - 点击「打印报表」触发 PDF 下载
   - 将下载的 PDF 保存到指定目录

## 说明
- 使用 Playwright (Python) 实现浏览器自动化，无需 Node.js。
- 默认以无头浏览器模式执行，如需可见模式可修改脚本中的 `headless=True` 为 `headless=False`。
- PDF 文件名格式自动生成，下载后会保存到配置的输出目录下。
