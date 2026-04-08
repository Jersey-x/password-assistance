import keyboard
import time
import json
import os
import sys
import threading
import socket
import webbrowser
import tkinter as tk
from tkinter import messagebox
from PIL import Image, ImageDraw
import pystray
from pystray import MenuItem as item
import requests

# --- 全局常量 ---
CONFIG_FILE = "pass_config.json"
CURRENT_VERSION = "1.0.0"

# --- 新增全局状态 ---
is_paused = False 
icon_instance = None

# --- 1. 单实例检测 (保持不变) ---
def is_already_running():
    try:
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_socket.bind(("127.0.0.1", 65432))
        globals()['_holder_socket'] = _lock_socket
        return False
    except socket.error:
        return True

# --- 2. 资源路径转换 ---
def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# --- 3. 配置管理 ---
def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            try: return json.load(f)
            except: return {}
    return {}

def save_config(entries, root):
    config = {key: entry.get() for key, entry in entries.items()}
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
    messagebox.showinfo("成功", "配置已保存！\n设置已实时生效。")
    refresh_listener() # 保存后立即刷新
    root.destroy()

# --- 4. 键盘监听逻辑 (核心修改) ---
def refresh_listener():
    """根据当前状态重新加载监听器"""
    keyboard.unhook_all()
    
    if is_paused:
        # 暂停状态下不注册热键，系统 F 键功能自然恢复
        return

    config = load_config()
    def make_send_func(pwd):
        def send():
            time.sleep(0.1) # 短暂延迟避免输入冲突
            keyboard.write(pwd)
        return send

    for key, pwd in config.items():
        if pwd:
            # suppress=True 拦截原生 F 键功能
            keyboard.add_hotkey(key, make_send_func(pwd), suppress=True)

# --- 5. 托盘图标逻辑 (新增暂停切换) ---
def on_toggle_pause(icon, item):
    global is_paused
    is_paused = not is_paused
    refresh_listener()
    # 状态改变后，手动通知图标刷新菜单文字
    icon.update_menu()

def get_pause_menu_label(item):
    return "▶ 恢复脚本" if is_paused else "⏸ 暂停脚本"

def create_icon():
    global icon_instance
    icon_name = "final_app.ico" 
    icon_path = get_resource_path(icon_name)

    try:
        image = Image.open(icon_path)
    except:
        image = Image.new('RGB', (64, 64), color=(0, 120, 215))
        draw = ImageDraw.Draw(image)
        draw.rectangle([16, 16, 48, 48], fill="white")

    # 创建菜单，使用函数作为标签实现动态更新
    menu = pystray.Menu(
        item(get_pause_menu_label, on_toggle_pause),
        item('设置密码', lambda: threading.Thread(target=show_settings, daemon=True).start()),
        item('退出程序', lambda icon, item: os._exit(0)),
    )
    
    icon_instance = pystray.Icon("PassAssistant", image, "快捷密码助手", menu)
    icon_instance.run()

# --- 6. GUI 设置界面 ---
def show_settings():
    root = tk.Tk()
    root.title(f"快捷键助手 v{CURRENT_VERSION}")
    root.geometry("380x650") 
    root.attributes("-topmost", True)
    root.resizable(False, False)

    # ... [此处保持你原来的 UI 代码不变] ...
    # 提醒：确保保存按钮调用的是修改后的 save_config
    
    # 示例简化布局
    list_frame = tk.LabelFrame(root, text=" 快捷键配置 ")
    list_frame.pack(fill="both", expand=True, padx=15, pady=5)
    
    entries = {}
    current_config = load_config()
    for i in range(1, 10):
        key = f"f{i}"
        f_row = tk.Frame(list_frame)
        f_row.pack(pady=2, fill='x')
        tk.Label(f_row, text=key.upper()).pack(side=tk.LEFT)
        ent = tk.Entry(f_row)
        ent.insert(0, current_config.get(key, ""))
        ent.pack(side=tk.RIGHT, expand=True)
        entries[key] = ent

    tk.Button(root, text="保 存 配 置", command=lambda: save_config(entries, root),
              bg="#28a745", fg="white").pack(pady=10)
    
    root.mainloop()

# --- 主程序入口 ---
if __name__ == "__main__":
    if is_already_running():
        temp_root = tk.Tk()
        temp_root.withdraw()
        messagebox.showwarning("提示", "程序已在后台运行。")
        sys.exit(0)

    # 初始加载监听器
    refresh_listener()

    # 启动托盘图标（会阻塞当前线程）
    create_icon()
