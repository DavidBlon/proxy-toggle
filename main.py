# -*- coding: utf-8 -*-
"""ProxyToggle：一键开关 Windows 命令行代理。"""

import ctypes
import json
import os
import sys
import threading
import tkinter as tk
from tkinter import messagebox, ttk

try:
    import winreg
except ImportError:
    winreg = None

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
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def load_config():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as file:
            return {**DEFAULT_CONFIG, **json.load(file)}
    except (OSError, ValueError, TypeError):
        return dict(DEFAULT_CONFIG)


def save_config(config):
    os.makedirs(CONFIG_DIR, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as file:
        json.dump(config, file, ensure_ascii=False, indent=2)


def _broadcast_env_change():
    result = ctypes.c_ulong()
    ctypes.windll.user32.SendMessageTimeoutW(
        0xFFFF, 0x001A, 0, "Environment", 0x0002, 5000, ctypes.byref(result)
    )


def get_proxy_status():
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
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
    ) as key:
        for variable in PROXY_VARS:
            winreg.SetValueEx(key, variable, 0, winreg.REG_SZ, proxy_url)
    _broadcast_env_change()


def disable_proxy():
    with winreg.OpenKey(
        winreg.HKEY_CURRENT_USER, "Environment", 0, winreg.KEY_SET_VALUE
    ) as key:
        for variable in PROXY_VARS:
            try:
                winreg.DeleteValue(key, variable)
            except OSError:
                pass
    _broadcast_env_change()


def _startup_command():
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}" --startup'
    script = os.path.abspath(__file__)
    executable = sys.executable
    if os.path.basename(executable).lower() == "python.exe":
        pythonw = os.path.join(os.path.dirname(executable), "pythonw.exe")
        if os.path.exists(pythonw):
            executable = pythonw
    return f'"{executable}" "{script}" --startup'


def is_startup_enabled():
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return bool(value)
    except OSError:
        return False


def set_startup_enabled(enabled):
    if winreg is None:
        raise OSError("开机自启仅支持 Windows")
    with winreg.CreateKeyEx(
        winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE
    ) as key:
        if enabled:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _startup_command())
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except FileNotFoundError:
                pass


def resource_path(relative_path):
    base = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, relative_path)


class ProxyToggleApp:
    def __init__(self):
        self.cfg = load_config()
        self.tray_icon = None
        self.root = tk.Tk()
        self.root.title(APP_NAME)
        self.root.resizable(False, False)
        self._set_window_icon()
        self._build_ui()
        self._refresh_status()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        if HAS_TRAY:
            self._start_tray()
            if "--startup" in sys.argv:
                self.root.withdraw()

    def _set_window_icon(self):
        icon_path = resource_path(os.path.join("assets", "proxy_toggle.ico"))
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except tk.TclError:
                pass

    def _build_ui(self):
        frame = ttk.Frame(self.root, padding=18)
        frame.grid(sticky="nsew")

        ttk.Label(frame, text="代理地址").grid(row=0, column=0, sticky="w", pady=5)
        self.host_var = tk.StringVar(value=self.cfg["host"])
        ttk.Entry(frame, textvariable=self.host_var, width=23).grid(
            row=1, column=0, sticky="ew", pady=(0, 8)
        )

        ttk.Label(frame, text="端口").grid(row=2, column=0, sticky="w", pady=5)
        self.port_var = tk.StringVar(value=self.cfg["port"])
        ttk.Entry(frame, textvariable=self.port_var, width=23).grid(
            row=3, column=0, sticky="ew", pady=(0, 10)
        )

        self.toggle_btn = ttk.Button(frame, command=self.toggle)
        self.toggle_btn.grid(row=4, column=0, pady=(4, 8), sticky="ew", ipady=3)

        self.status_var = tk.StringVar()
        self.status_lbl = ttk.Label(frame, textvariable=self.status_var, anchor="center")
        self.status_lbl.grid(row=5, column=0, pady=4, sticky="ew")

        ttk.Separator(frame).grid(row=6, column=0, pady=(10, 8), sticky="ew")
        self.startup_var = tk.BooleanVar(value=is_startup_enabled())
        ttk.Checkbutton(
            frame,
            text="开机时自动启动（静默到托盘）",
            variable=self.startup_var,
            command=self._toggle_startup,
        ).grid(row=7, column=0, sticky="w")

        ttk.Label(
            frame,
            text="代理设置仅对新打开的终端窗口生效",
            foreground="gray",
        ).grid(row=8, column=0, pady=(12, 0))

    def _toggle_startup(self):
        requested = self.startup_var.get()
        try:
            set_startup_enabled(requested)
        except OSError as error:
            self.startup_var.set(not requested)
            messagebox.showerror(APP_NAME, f"设置开机自启失败：{error}")

    def _refresh_status(self):
        current = get_proxy_status()
        if current:
            self.status_var.set(f"● 代理已开启  {current}")
            self.status_lbl.configure(foreground="#159447")
            self.toggle_btn.configure(text="关闭代理")
        else:
            self.status_var.set("● 代理已关闭")
            self.status_lbl.configure(foreground="#777777")
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
                if not host or not port.isdigit() or not 0 < int(port) < 65536:
                    messagebox.showwarning(APP_NAME, "请输入有效的地址和端口（1-65535）")
                    return
                self.cfg = {"host": host, "port": port}
                save_config(self.cfg)
                enable_proxy(host, port)
        except OSError as error:
            messagebox.showerror(APP_NAME, f"操作失败：{error}")
        self._refresh_status()

    def _start_tray(self):
        menu = pystray.Menu(
            pystray.MenuItem("显示主窗口", self._show_window, default=True),
            pystray.MenuItem("开启 / 关闭代理", self._tray_toggle),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", self._quit),
        )
        self.tray_icon = pystray.Icon(
            APP_NAME, _make_tray_image(bool(get_proxy_status())), APP_NAME, menu
        )
        threading.Thread(target=self.tray_icon.run, daemon=True).start()

    def _show_window(self, *_):
        self.root.after(0, lambda: (self.root.deiconify(), self.root.lift()))

    def _tray_toggle(self, *_):
        self.root.after(0, self.toggle)

    def _on_close(self):
        if self.tray_icon is not None:
            self.root.withdraw()
        else:
            self._quit()

    def _quit(self, *_):
        if self.tray_icon is not None:
            self.tray_icon.stop()
        self.root.after(0, self.root.destroy)

    def run(self):
        self.root.mainloop()


def _make_tray_image(enabled):
    size = 64
    accent = (37, 211, 102, 255) if enabled else (107, 114, 128, 255)
    image = Image.new("RGBA", (size, size), (14, 23, 38, 255))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((3, 3, 60, 60), radius=15, fill=(14, 23, 38, 255))
    draw.line((17, 22, 47, 22), fill=accent, width=7)
    draw.line((17, 42, 47, 42), fill=accent, width=7)
    draw.ellipse((10, 15, 24, 29), fill=(245, 247, 250, 255))
    draw.ellipse((40, 35, 54, 49), fill=(245, 247, 250, 255))
    draw.line((22, 27, 42, 37), fill=accent, width=5)
    return image


if __name__ == "__main__":
    ProxyToggleApp().run()
