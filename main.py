import sys
import os
import subprocess

import keyboard
from PySide6.QtCore import Qt, QObject, Signal, QTimer
from PySide6.QtWidgets import QApplication, QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor

from config import load_config, save_config
from ui.popup import PopupMenu
from ui.startup_animation import StartupAnimation


class HotkeyBridge(QObject):
    triggered = Signal()


def make_tray_icon(accent_color):
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor(accent_color))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    painter.end()
    return QIcon(pixmap)


def launch_app(path):
    try:
        os.startfile(path)
    except Exception:
        subprocess.Popen(path, shell=True)


AUTOSTART_NAME = 'Minisist'
AUTOSTART_KEY_PATH = r'Software\Microsoft\Windows\CurrentVersion\Run'


def _startup_command():
    if getattr(sys, 'frozen', False):
        return f'"{sys.executable}"'
    script_path = os.path.abspath(sys.argv[0])
    return f'"{sys.executable}" "{script_path}"'


def sync_autostart(enabled):
    try:
        import winreg
    except ImportError:
        print("Minisist: autostart requires Windows (winreg unavailable)")
        return
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, AUTOSTART_KEY_PATH, 0, winreg.KEY_SET_VALUE)
    except OSError as e:
        print(f"Minisist: could not open registry Run key: {e}")
        return
    try:
        if enabled:
            winreg.SetValueEx(key, AUTOSTART_NAME, 0, winreg.REG_SZ, _startup_command())
            print("Minisist: autostart enabled")
        else:
            try:
                winreg.DeleteValue(key, AUTOSTART_NAME)
                print("Minisist: autostart disabled")
            except FileNotFoundError:
                pass
    except OSError as e:
        print(f"Minisist: failed to update autostart: {e}")
    finally:
        winreg.CloseKey(key)


class MinisistApp:
    def __init__(self):
        self.config = load_config()
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)

        self.bridge = HotkeyBridge()
        self.bridge.triggered.connect(self._toggle_popup)

        self._preview_ref = None
        self.popup = None
        self._create_popup()

        self.tray = QSystemTrayIcon(make_tray_icon(self.config['accent_color']))
        tray_menu = QMenu()
        open_action = tray_menu.addAction('Open Menu')
        open_action.triggered.connect(self._toggle_popup)
        settings_action = tray_menu.addAction('Settings')
        settings_action.triggered.connect(self._open_settings_from_tray)
        tray_menu.addSeparator()
        quit_action = tray_menu.addAction('Quit')
        quit_action.triggered.connect(self.app.quit)
        self.tray.setContextMenu(tray_menu)
        self.tray.activated.connect(self._on_tray_activated)
        self.tray.show()

        self._register_hotkey(self.config['hotkey'])
        sync_autostart(self.config.get('start_with_windows', False))

    def _create_popup(self):
        self.popup = PopupMenu(self.config, self._save_config, launch_app, self._preview_animation,
                                on_closed=self._handle_popup_closed)

    def _ensure_popup(self):
        if self.popup is None:
            print("Minisist: performance mode - reloading menu")
            self._create_popup()
        return self.popup

    def _handle_popup_closed(self):
        if self.config.get('performance_mode'):
            QTimer.singleShot(0, self._teardown_popup)

    def _teardown_popup(self):
        if self.popup is not None:
            print("Minisist: performance mode - unloading menu")
            popup = self.popup
            self.popup = None
            popup.deleteLater()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._toggle_popup()

    def _register_hotkey(self, hotkey):
        try:
            keyboard.unhook_all_hotkeys()
        except Exception:
            pass
        try:
            keyboard.add_hotkey(hotkey, lambda: self.bridge.triggered.emit())
            print(f"Minisist: hotkey '{hotkey}' registered")
        except Exception as e:
            print(f"Minisist: failed to register hotkey '{hotkey}': {e}")
            print("Minisist: try running this terminal as Administrator")

    def _toggle_popup(self):
        print("Minisist: hotkey triggered")
        popup = self._ensure_popup()
        popup.toggle()

    def _open_settings_from_tray(self):
        popup = self._ensure_popup()
        popup.show_settings()

    def _save_config(self, new_config):
        self.config = new_config
        save_config(self.config)
        self._register_hotkey(self.config['hotkey'])
        sync_autostart(self.config.get('start_with_windows', False))
        if self.popup is not None:
            self.popup.refresh(self.config)
        self.tray.setIcon(make_tray_icon(self.config['accent_color']))

    def _preview_animation(self, accent_color, background_color):
        self._preview_ref = StartupAnimation(accent_color, background_color)
        self._preview_ref.start()

    def run(self):
        sys.exit(self.app.exec())


if __name__ == '__main__':
    MinisistApp().run()
