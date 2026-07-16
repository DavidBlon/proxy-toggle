# ProxyToggle

一键开关 Windows 命令行代理的小工具。

## 功能

- 一键设置或移除 `HTTP_PROXY` / `HTTPS_PROXY` 用户环境变量
- 自定义代理地址和端口，配置保存在 `%APPDATA%\ProxyToggle\config.json`
- 系统托盘快捷开关代理
- 可选“开机时自动启动”，自启后静默进入系统托盘
- 多分辨率应用图标，同时用于 EXE、窗口和系统托盘
- 仅修改当前用户配置，不需要管理员权限

代理设置只对新打开的 cmd、PowerShell 和其他命令行程序生效。

## 直接运行

```bat
pip install -r requirements.txt
python main.py
```

## 打包 EXE

双击 `build.bat`，或执行：

```bat
pip install -r requirements.txt pyinstaller
pyinstaller --clean --noconfirm ProxyToggle.spec
```

产物位于 `dist\ProxyToggle.exe`。如需重新生成图标，可先运行：

```bat
python generate_icon.py
```

## 开机自启原理

勾选后，程序在当前用户注册表
`HKCU\Software\Microsoft\Windows\CurrentVersion\Run` 中写入启动项；取消勾选后会删除该启动项。打包版开机启动时会携带 `--startup` 参数并直接缩到托盘。
