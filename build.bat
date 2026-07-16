@echo off
chcp 65001 >nul
cd /d %~dp0
pip install -r requirements.txt pyinstaller
for /f "delims=" %%i in ('python -c "import sys; print(sys.base_prefix)"') do set "PYTHON_ROOT=%%i"
set "TCL_LIBRARY=%PYTHON_ROOT%\tcl\tcl8.6"
set "TK_LIBRARY=%PYTHON_ROOT%\tcl\tk8.6"
pyinstaller --clean --noconfirm ProxyToggle.spec
echo.
echo 打包完成，产物位于 dist\ProxyToggle.exe
pause
