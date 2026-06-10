# JMate 打包命令记录

## 1. 稳定版：无 UPX

```powershell
Remove-Item build,dist -Recurse -Force -ErrorAction SilentlyContinue

python -m PyInstaller --clean --noconfirm --noupx --onedir --windowed --name JMate `
  --collect-binaries shiboken6 `
  --hidden-import shiboken6.Shiboken `
  --hidden-import PySide6.QtCore `
  --hidden-import PySide6.QtGui `
  --hidden-import PySide6.QtWidgets `
  --add-data "frontend;frontend" `
  --add-data "shared;shared" `
  --add-data "backend;backend" `
  main.py
```

## 2. UPX 测试版


```powershell
Remove-Item build,dist_upx -Recurse -Force -ErrorAction SilentlyContinue

python -m PyInstaller --clean --noconfirm --onedir --windowed --name JMate `
  --distpath dist_upx `
  --collect-binaries shiboken6 `
  --hidden-import shiboken6.Shiboken `
  --hidden-import PySide6.QtCore `
  --hidden-import PySide6.QtGui `
  --hidden-import PySide6.QtWidgets `
  --upx-exclude "python3.dll" `
  --upx-exclude "python312.dll" `
  --upx-exclude "Qt6Core.dll" `
  --upx-exclude "Qt6Gui.dll" `
  --upx-exclude "Qt6Widgets.dll" `
  --upx-exclude "shiboken6.abi3.dll" `
  --upx-exclude "Shiboken.pyd" `
  --upx-exclude "VCRUNTIME140.dll" `
  --upx-exclude "VCRUNTIME140_1.dll" `
  --upx-exclude "MSVCP140.dll" `
  --upx-exclude "api-ms-win-crt-*.dll" `
  --add-data "frontend;frontend" `
  --add-data "shared;shared" `
  --add-data "backend;backend" `
  main.py
```