@echo off
chcp 65001 >nul
cd /d %~dp0
pip install -r requirements.txt pyinstaller
pyinstaller --clean --noconfirm ProxyToggle.spec
echo.
echo 打包完成，产物位于 dist\ProxyToggle.exe
pause
