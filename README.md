# J-Mate PySide6 Desktop Frontend

这是根据 `J-Mete(1).html` 页面布局重写的 Python + PySide6 桌面前端框架。项目只实现可运行的 GUI 展示和基础交互，不包含 Agent、模型调用、API 请求或真实业务逻辑。

## 安装依赖

```bash
pip install -r requirements.txt
```

## 运行

```bash
python main.py
```

## 结构

```text
agent/
├── main.py
├── requirements.txt
├── app/
│   ├── main_window.py
│   ├── state.py
│   └── theme.py
├── views/
│   └── chat_view.py
├── widgets/
│   ├── header_bar.py
│   ├── input_bar.py
│   ├── message_bubble.py
│   ├── settings_dialog.py
│   └── skill_chip.py
├── resources/
│   └── styles/
│       └── app.qss
└── utils/
    └── paths.py
```
