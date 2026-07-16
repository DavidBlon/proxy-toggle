# -*- coding: utf-8 -*-
"""ProxyToggle - 一键开关 cmd 命令行代理（Windows）

原理：写入/删除 HKCU\\Environment 下的用户级环境变量
HTTP_PROXY / HTTPS_PROXY（及小写变体），并广播 WM_SETTINGCHANGE，
使新打开的 cmd / PowerShell 窗口生效。
"""

import ctypes
import json
import os
import threading
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import winreg
except ImportError:
    winreg = None  # 非 Windows 平台（仅供预览界面）

# 托盘为可选依赖，缺失时自动退化为纯窗口模式
try:
    import pystray
    from PIL import Image, ImageDraw
    HAS_TRAY = True
except ImportError:
    HAS_TRAY = False

APP_NAME = "ProxyToggle"
PROXY_VARS = ["HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"]
CONFIG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), APP_NAME)
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
DEFAULT_CONFIG = {"host": "127.0.0.1", "port": "7890"}


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return {**DEFAULT_CONFIG, **json.load(f)}
    except (OSError, ValueError):
        return dict(DEFAULT_CONFIG)


def save_config(cfg):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)


def _broadcast_env_change():
    """通知系统环境变量已变更，使新开的 cmd 读取到新值。"""
    ctypes.windll.user32.SendMessageTimeoutW(
        0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000,
        ctypes.byref(ctypes.c_ulong()))


def get_proxy_status():
    """返回当前用户环境变量中的代理地址，未设置返回 None。"""
    if winreg is None:
        return None
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, _ = winreg.QueryValueEx(key, "HTTP_PROXY")
            return value or None
    except OSError:
        return None


def enable_proxy(host, port):
    proxy_url = f"http://{host}:{port}"
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                        winreg.KEY_SET_VALUE) as key:
        for var in PROXY_VARS:
            winreg.SetValueEx(key, var, 0, winreg.REG_SZ, proxy_url)
    _broadcast_env_change()


def disable_proxy():
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment", 0,
                        winreg.KEY_SET_VALUE) as key:
        for var in PROXY_VARS:
            try:
                winreg.DeleteValue(key, var)
            except OSError:
                pass  # 变量本就不存在
    _broadcast_env_change()


class ProxyToggleApp:
    def __init__(self):
        self.cfg = load_config()
        self.tray_icon = None

        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.resizable(False, False)
        self._build_ui()
        self._refresh_status()
        # 点关闭按钮：有托盘则最小化到托盘，否则退出
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        if HAS_TRAY:
            self._start_tray()

    def _build_ui(self):
        frm = ttk.Frame(self.root, padding=16)
        frm.grid(sticky="nsew")

        ttk.Label(frm, text="代理地址:").grid(row=0, column=0, sticky="e", pady=4)
        self.host_var = tk.StringVar(value=self.cfg["host"])
        ttk.Entry(frm, textvariable=self.host_var, width=18).grid(
            row=0, column=1, sticky="w", pady=4)

        ttk.Label(frm, text="端口:").grid(row=1, column=0, sticky="e", pady=4)
        self.port_var = tk.StringVar(value=self.cfg["port"])
        ttk.Entry(frm, textvariable=self.port_var, width=18).grid(
            row=1, column=1, sticky="w", pady=4)

        self.toggle_btn = ttk.Button(frm, text="开启代理", command=self.toggle)
        self.toggle_btn.grid(row=2, column=0, columnspan=2, pady=(12, 4), sticky="ew")

        self.status_var = tk.StringVar()
        self.status_lbl = ttk.Label(frm, textvariable=self.status_var, anchor="center")
        self.status_lbl.grid(row=3, column=0, columnspan=2, pady=(4, 0), sticky="ew")

        ttk.Label(frm, text="提示: 开关后仅对新打开的 cmd/PowerShell 窗口生效",
                  foreground="gray").grid(row=4, column=0, columnspan=2, pady=(8, 0))

    def _refresh_status(self):
        current = get_proxy_status()
        if current:
            self.status_var.set(f"✅ 代理已开启: {current}")
            self.status_lbl.configure(foreground="green")
            self.toggle_btn.configure(text="关闭代理")
        else:
            self.status_var.set("⛔ 代理已关闭")
            self.status_lbl.configure(foreground="red")
            self.toggle_btn.configure(text="开启代理")
        if self.tray_icon is not None:
            self.tray_icon.icon = _make_tray_image(bool(current))
            self.tray_icon.title = f"{APP_NAME} - {'已开启' if current else '已关闭'}"

    def toggle(self):
        if winreg is None:
            messagebox.showerror(APP_NAME, "本工具仅支持 Windows 系统")
            return
        try:
            if get_proxy_status():
                disable_proxy()
            else:
                host = self.host_var.get().strip()
                port = self.port_var.get().strip()
                if not host or not port.isdigit() or not (0 < int(port) < 65536):
                    messagebox.showwarning(APP_NAME, "请输入有效的地址和端口 (1-65535)")
                    return
                self.cfg = {"host": host, "port": port}
                save_config(self.cfg)
                enable_proxy(host, port)
        except OSError as e:
            messagebox.showerror(APP_NAME, f"操作失败: {e}")
        self._refresh_status()

    def _start_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", self._show_window, default=True),
            pystray.MenuItem("开/关代理", self._tray_toggle),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._quit),
        )
        self.tray_icon = pystray.Icon(
            APP_NAME, _make_tray_image(bool(get_proxy_status())), APP_NAME, menu)
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _show_window(self, *_):
        self.root.after(0, lambda: (self.root.deiconify(), self.root.lift()))

    def _tray_toggle(self, *_):
        self.root.after(0, self.toggle)

    def _on_close(self):
        if self.tray_icon is not None:
            self.root.withdraw()  # 最小化到托盘
        else:
            self._quit()

    def _quit(self, *_):
        if self.tray_icon is not None:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def run(self):
        self.root.mainloop()


def _make_tray_image(enabled):
    """托盘图标：绿色=开启，灰色=关闭。"""
    color = (0, 170, 0) if enabled else (128, 128, 128)
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((8, 8, 56, 56), fill=color)
    d.text((24, 16), "P", fill="white")
    return img


if __name__ == "__main__":
    ProxyToggleApp().run()
