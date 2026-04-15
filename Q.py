import sys
import os
import json
import time
import threading
import socket
import webbrowser
import requests
import keyboard
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                             QScrollArea, QMessageBox, QFrame, QSystemTrayIcon, QMenu)
from PyQt6.QtCore import Qt, pyqtProperty, QPropertyAnimation, QEasingCurve, QObject, pyqtSignal
from PyQt6.QtGui import QIcon, QAction

# --- 全局常量 ---
CONFIG_FILE = "密码配置文件.json"
CURRENT_VERSION = "1.0.0"
GITHUB_USER = "Jerseyx"
GITHUB_REPO = "password-assistance"
VERSION_URL = f"https://raw.githubusercontent.com/{GITHUB_USER}/{GITHUB_REPO}/refs/heads/main/version.txt"
DOWNLOAD_URL = f"https://github.com/{GITHUB_USER}/{GITHUB_REPO}/releases"

is_paused = False

# --- 信号处理 ---
class UpdateSignals(QObject):
    update_found = pyqtSignal(str)
    no_update = pyqtSignal()
    network_error = pyqtSignal(str)

signals = UpdateSignals()

# --- 1. 基础逻辑函数 ---
def is_already_running():
    try:
        _lock_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        _lock_socket.bind(("127.0.0.1", 65432))
        globals()['_holder_socket'] = _lock_socket
        return False
    except socket.error:
        return True

def get_resource_path(relative_path):
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {}

def start_keyboard_listener():
    keyboard.unhook_all()
    if is_paused:
        return
    config = load_config()
    for key, pwd in config.items():
        if pwd:
            # 闭包处理：确保每个快捷键对应正确的密码
            def make_write_func(p):
                return lambda: (time.sleep(0.05), keyboard.write(p))
            keyboard.add_hotkey(key, make_write_func(pwd), suppress=True)

# --- 2. 核心动效控件 (选中填充) ---
class AnimatedLineEdit(QLineEdit):
    """自定义带焦点填充动画的输入框"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._fill_percent = 0
        self.setMinimumHeight(40)
        self.update_style()

    @pyqtProperty(int)
    def fill_percent(self):
        return self._fill_percent

    @fill_percent.setter
    def fill_percent(self, value):
        self._fill_percent = value
        self.update_style()

    def update_style(self):
        pos = self._fill_percent / 100.0
        # 只有在有焦点或动画进行中时变色
        border_color = "#000000" if self.hasFocus() or self._fill_percent > 0 else "#DCDCDC"
        
        self.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {border_color};
                border-radius: 8px;
                padding: 8px 12px;
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                            stop:0 #E3F2FD, stop:{pos} #E3F2FD, 
                            stop:{min(pos + 0.001, 1.0)} #FFFFFF, stop:1 #FFFFFF);
                font-family: "Microsoft YaHei", "Segoe UI";
                font-size: 13px;
            }}
        """)

    def focusInEvent(self, event):
        # 选中时触发填充动画
        self.ani = QPropertyAnimation(self, b"fill_percent")
        self.ani.setDuration(400)
        self.ani.setStartValue(self._fill_percent)
        self.ani.setEndValue(100)
        self.ani.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.ani.start()
        super().focusInEvent(event)

    def focusOutEvent(self, event):
        # 失去焦点时退回
        self.ani = QPropertyAnimation(self, b"fill_percent")
        self.ani.setDuration(300)
        self.ani.setStartValue(self._fill_percent)
        self.ani.setEndValue(0)
        self.ani.setEasingCurve(QEasingCurve.Type.InQuad)
        self.ani.start()
        super().focusOutEvent(event)

# --- 3. 设置界面 ---
class SettingsWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle(f"快捷密码助手 v{CURRENT_VERSION}")
        self.setFixedSize(420, 700)
        self.setWindowIcon(QIcon(get_resource_path("final_app.ico")))
        self.setStyleSheet("QMainWindow { background-color: #FFFFFF; }")
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(20)

        # 头部说明
        header = QLabel("配置快捷按键")
        header.setStyleSheet("font-size: 20px; font-weight: bold; color: #1A1A1A;")
        main_layout.addWidget(header)

        # 列表区
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setStyleSheet("background: transparent;")
        
        container = QWidget()
        container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(container)
        self.list_layout.setSpacing(12)
        
        self.entries = {}
        config = load_config()
        
        for i in range(1, 10):
            key = f"f{i}"
            row = QHBoxLayout()
            label = QLabel(key.upper())
            label.setFixedWidth(40)
            label.setStyleSheet("font-weight: bold; color: #777;")
            
            edit = AnimatedLineEdit()
            edit.setText(config.get(key, ""))
            edit.setPlaceholderText(f"请输入按下 {key.upper()} 后的密码...")
            
            row.addWidget(label)
            row.addWidget(edit)
            self.entries[key] = edit
            self.list_layout.addLayout(row)
            
        scroll.setWidget(container)
        main_layout.addWidget(scroll)

        # 底部按钮
        btn_save = QPushButton("保 存 全 部 设 置")
        btn_save.setFixedHeight(50)
        btn_save.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2D2D2D;
                color: white;
                border-radius: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover { background-color: #454545; }
            QPushButton:pressed { background-color: #000000; }
        """)
        btn_save.clicked.connect(self.save_settings)
        main_layout.addWidget(btn_save)

    def save_settings(self):
        config = {key: edit.text() for key, edit in self.entries.items()}
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)
        QMessageBox.information(self, "成功", "设置已实时生效！")
        start_keyboard_listener()
        self.close()

# --- 4. 检查更新 ---
def check_update(manual=False):
    def _run():
        try:
            res = requests.get(VERSION_URL, timeout=5)
            if res.status_code == 200:
                remote_v = res.text.strip()
                if remote_v > CURRENT_VERSION:
                    signals.update_found.emit(remote_v)
                elif manual: signals.no_update.emit()
        except Exception:
            if manual: signals.network_error.emit("连接失败")
    threading.Thread(target=_run, daemon=True).start()

# --- 5. 托盘管理 ---
class TrayApp:
    def __init__(self, app):
        self.app = app
        self.window = None
        self.tray_icon = QSystemTrayIcon(QIcon(get_resource_path("final_app.ico")), self.app)
        
        menu = QMenu()
        self.pause_act = QAction("⏸ 暂停脚本", menu)
        self.pause_act.triggered.connect(self.toggle_pause)
        
        set_act = QAction("⚙ 设置密码", menu)
        set_act.triggered.connect(self.show_settings)
        
        exit_act = QAction("❌ 退出程序", menu)
        exit_act.triggered.connect(QApplication.quit)
        
        menu.addAction(self.pause_act)
        menu.addAction(set_act)
        menu.addSeparator()
        menu.addAction(exit_act)
        
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()

        signals.update_found.connect(self.on_update)
        signals.no_update.connect(lambda: QMessageBox.information(None, "提示", "目前已是最新版本"))

    def toggle_pause(self):
        global is_paused
        is_paused = not is_paused
        self.pause_act.setText("▶ 恢复脚本" if is_paused else "⏸ 暂停脚本")
        start_keyboard_listener()

    def show_settings(self):
        if not self.window: self.window = SettingsWindow()
        self.window.show()
        self.window.activateWindow()

    def on_update(self, v):
        if QMessageBox.question(None, "更新", f"发现新版本 {v}，是否前往下载？") == QMessageBox.StandardButton.Yes:
            webbrowser.open(DOWNLOAD_URL)

# --- 主程序入口 ---
if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    if is_already_running():
        QMessageBox.warning(None, "提示", "程序已在后台运行中，请检查右下角托盘！")
        sys.exit(0)

    start_keyboard_listener()
    tray = TrayApp(app)

    # 首次运行或配置文件不存在时自动打开窗口
    if not os.path.exists(CONFIG_FILE):
        tray.show_settings()

    check_update(manual=False)
    sys.exit(app.exec())