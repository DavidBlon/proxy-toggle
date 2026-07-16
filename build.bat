@echo off
:: 打包 ProxyToggle 为独立 exe（需先 pip install pyinstaller）
cd /d %~dp0
pip install -r requirements.txt pyinstaller
pyinstaller --onefile --noconsole --name ProxyToggle main.py
echo.
echo 打包完成，产物在 dist\ProxyToggle.exe
pause
