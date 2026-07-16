# ProxyToggle

一键开关 cmd 命令行代理的 Windows 小工具，支持自定义代理地址和端口。

## 功能

- 一键开启/关闭命令行代理（`HTTP_PROXY` / `HTTPS_PROXY` 用户环境变量）
- 自定义代理地址和端口，配置自动保存到 `%APPDATA%\ProxyToggle\config.json`
- 实时显示当前代理状态（绿色=已开启，红色=已关闭）
- 系统托盘图标：关闭窗口自动缩到托盘，托盘右键可快速开关代理或退出
- 不需要管理员权限（只修改当前用户的环境变量）

## 原理

写入/删除注册表 `HKCU\Environment` 下的 `HTTP_PROXY`、`HTTPS_PROXY`
（及小写变体）环境变量，并广播 `WM_SETTINGCHANGE` 消息。
git、curl、npm、pip、node 等命令行工具都会读取这组变量。

> 注意：开关后仅对**新打开的** cmd / PowerShell 窗口生效，
> 已打开的窗口不会自动刷新（Windows 机制限制）。

## 直接运行

```bat
pip install -r requirements.txt
python main.py
```

不安装 pystray/Pillow 也能运行，只是没有托盘图标（纯窗口模式）。

## 打包为独立 exe

双击运行 `build.bat`，或手动执行：

```bat
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --noconsole --name ProxyToggle main.py
```

产物为 `dist\ProxyToggle.exe`（约 10-15 MB），单文件免安装，可拷到任何 Windows 电脑使用。

## 使用

1. 启动后输入代理地址（默认 `127.0.0.1`）和端口（默认 `7890`）
2. 点「开启代理」；新开一个 cmd 输入 `echo %HTTP_PROXY%` 验证
3. 再点一次「关闭代理」即可移除
4. 点窗口关闭按钮会缩到托盘，托盘右键 →「退出」才是真正退出
