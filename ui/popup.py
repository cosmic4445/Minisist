import os
import subprocess

import psutil
from PySide6.QtCore import Qt, QTimer, QPoint, QSize, QPropertyAnimation, QEasingCurve, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QColor, QGuiApplication, QCursor, QLinearGradient, QRadialGradient, QIcon
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QGraphicsOpacityEffect, QStackedWidget
)

from ui.startup_animation import LogoWidget, build_boot_animation, build_draw_in_animation
from ui.settings import SettingsPage

ICONS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'assets', 'icons')

WIDTH = 300
HEIGHT = 460
CORNER_RADIUS = 18
SLIDE_DISTANCE = 90
SLIDE_DURATION = 320
CONTENT_FADE_DURATION = 300


def compute_target_position(width=WIDTH, height=HEIGHT):
    screen = QGuiApplication.screenAt(QCursor.pos())
    if screen is None:
        screen = QGuiApplication.primaryScreen()
    area = screen.geometry()
    x = area.right() - width + 1
    y = area.bottom() - height + 1
    return QPoint(x, y)


def _rounded_top_left_path(width, height, radius):
    path = QPainterPath()
    path.moveTo(0, radius)
    path.arcTo(0, 0, radius * 2, radius * 2, 180, -90)
    path.lineTo(width, 0)
    path.lineTo(width, height)
    path.lineTo(0, height)
    path.closeSubpath()
    return path


class RoundedPanel(QWidget):
    def __init__(self, accent_color, bg_color, parent=None):
        super().__init__(parent)
        self.accent_color = QColor(accent_color)
        self.bg_color = QColor(bg_color)

    def set_colors(self, accent_color, bg_color):
        self.accent_color = QColor(accent_color)
        self.bg_color = QColor(bg_color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = _rounded_top_left_path(self.width(), self.height(), CORNER_RADIUS)
        painter.setClipPath(path)

        gradient = QLinearGradient(0, 0, 0, self.height())
        gradient.setColorAt(0, self.bg_color.lighter(122))
        gradient.setColorAt(1, self.bg_color)
        painter.fillPath(path, gradient)

        glow = QRadialGradient(36, 34, 170)
        glow_color = QColor(self.accent_color)
        glow_color.setAlpha(55)
        glow.setColorAt(0, glow_color)
        faded = QColor(self.accent_color)
        faded.setAlpha(0)
        glow.setColorAt(1, faded)
        painter.fillRect(self.rect(), glow)


class BootOverlay(QWidget):
    def __init__(self, accent_color, bg_color, parent=None):
        super().__init__(parent)
        self.bg_color = QColor(bg_color)
        self.logo = LogoWidget(accent_color, bg_color, self, size=120)

    def set_colors(self, accent_color, bg_color):
        self.bg_color = QColor(bg_color)
        self.logo.accent_color = QColor(accent_color)
        self.logo.bg_color = QColor(bg_color)
        self.update()

    def resizeEvent(self, event):
        self.logo.move((self.width() - self.logo.width()) // 2, (self.height() - self.logo.height()) // 2)
        super().resizeEvent(event)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        path = _rounded_top_left_path(self.width(), self.height(), CORNER_RADIUS)
        painter.fillPath(path, self.bg_color)


class BoxFrame(QFrame):
    def __init__(self, title=None, accent_stripe=False):
        super().__init__()
        self.accent_stripe = accent_stripe
        self.accent_color = QColor('#22c55e')
        self._apply_style()
        self.layout_inner = QVBoxLayout(self)
        self.layout_inner.setContentsMargins(12, 8, 10, 10)
        self.layout_inner.setSpacing(6)
        if title:
            label = QLabel(title.upper())
            label.setStyleSheet("color: #888; font-size: 10px; letter-spacing: 1px; border: none; background: transparent;")
            self.layout_inner.addWidget(label)

    def _apply_style(self):
        border_left = f"3px solid {self.accent_color.name()}" if self.accent_stripe else "1px solid rgba(255,255,255,0.08)"
        self.setStyleSheet(f"""
            QFrame {{
                background: rgba(255,255,255,0.045);
                border: 1px solid rgba(255,255,255,0.08);
                border-left: {border_left};
                border-radius: 10px;
            }}
        """)

    def set_accent(self, color):
        self.accent_color = QColor(color)
        self._apply_style()


class StatBar(QWidget):
    def __init__(self, label, accent_color):
        super().__init__()
        self.label = label
        self.accent_color = QColor(accent_color)
        self.percent = 0
        self.setFixedHeight(30)

    def set_percent(self, value):
        self.percent = max(0, min(100, value))
        self.update()

    def set_accent(self, color):
        self.accent_color = QColor(color)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        painter.setPen(QColor(210, 210, 210))
        text_rect = QRectF(0, 0, self.width(), 16)
        painter.drawText(text_rect, Qt.AlignLeft | Qt.AlignVCenter, f"{self.label}: {self.percent:.0f}%")

        track_rect = QRectF(0, 20, self.width(), 6)
        track_path = QPainterPath()
        track_path.addRoundedRect(track_rect, 3, 3)
        painter.fillPath(track_path, QColor(255, 255, 255, 22))

        fill_width = track_rect.width() * (self.percent / 100)
        if fill_width > 1:
            fill_rect = QRectF(track_rect.x(), track_rect.y(), fill_width, track_rect.height())
            fill_path = QPainterPath()
            fill_path.addRoundedRect(fill_rect, 3, 3)
            painter.fillPath(fill_path, self.accent_color)


class MainPage(QWidget):
    def __init__(self, config, on_open_settings, on_system_action, on_launch_app):
        super().__init__()
        self.config = config
        self.on_open_settings = on_open_settings
        self.on_system_action = on_system_action
        self.on_launch_app = on_launch_app

        self.layout_root = QVBoxLayout(self)
        self.layout_root.setContentsMargins(18, 16, 18, 18)
        self.layout_root.setSpacing(12)

        header = QHBoxLayout()
        self.mini_logo = LogoWidget(config['accent_color'], config['background_color'], size=30)
        header.addWidget(self.mini_logo)
        header.addStretch()
        settings_btn = QPushButton('⚙')
        settings_btn.setFixedSize(28, 28)
        settings_btn.setStyleSheet("QPushButton { background: transparent; color: #ccc; border: none; font-size: 15px; } QPushButton:hover { color: white; }")
        settings_btn.clicked.connect(self.on_open_settings)
        header.addWidget(settings_btn)
        self.settings_btn = settings_btn
        self.layout_root.addLayout(header)

        stats_box = BoxFrame()
        self.memory_bar = StatBar('Memory', config['accent_color'])
        self.cpu_bar = StatBar('CPU', config['accent_color'])
        stats_box.layout_inner.addWidget(self.memory_bar)
        stats_box.layout_inner.addWidget(self.cpu_bar)
        self.layout_root.addWidget(stats_box)

        self.apps_box = BoxFrame('Apps', accent_stripe=True)

        self.other_apps_box = BoxFrame('Other Apps')
        self.other_apps_container = QVBoxLayout()
        self.other_apps_container.setSpacing(4)
        self.other_apps_box.layout_inner.addLayout(self.other_apps_container)
        self.apps_box.layout_inner.addWidget(self.other_apps_box)

        self.utility_container = QVBoxLayout()
        self.utility_container.setSpacing(4)
        self.utility_buttons = {}
        utilities = [
            ('File Explorer', 'explorer', 'file_explorer.png'),
            ('Task Manager', 'taskmanager', 'task_manager.png'),
            ('Control Panel', 'controlpanel', 'control_panel.png'),
            ('Windows Settings', 'settings', 'windows_settings.png'),
        ]
        for label, action, icon_file in utilities:
            btn = QPushButton(label)
            icon_path = os.path.join(ICONS_DIR, icon_file)
            if os.path.exists(icon_path):
                btn.setIcon(QIcon(icon_path))
                btn.setIconSize(QSize(16, 16))
            btn.setStyleSheet(self._utility_btn_style())
            btn.clicked.connect(lambda checked=False, a=action: self._handle_system(a))
            self.utility_container.addWidget(btn)
            self.utility_buttons[label] = btn
        self.apps_box.layout_inner.addLayout(self.utility_container)

        self.layout_root.addWidget(self.apps_box)
        self.layout_root.addStretch()

        self._apply_theme()
        self._render_other_apps()

    def _utility_btn_style(self):
        return """
            QPushButton {
                text-align: left;
                background: rgba(255,255,255,0.06);
                color: #eee;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
                padding: 7px 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.16);
                border: 1px solid rgba(255,255,255,0.2);
            }
        """

    def _apply_theme(self):
        accent = self.config['accent_color']
        self.mini_logo.accent_color = QColor(accent)
        self.mini_logo.bg_color = QColor(self.config['background_color'])
        self.mini_logo.update()
        self.memory_bar.set_accent(accent)
        self.cpu_bar.set_accent(accent)
        self.apps_box.set_accent(accent)

    def _render_other_apps(self):
        while self.other_apps_container.count():
            item = self.other_apps_container.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        apps = self.config.get('apps', [])
        if not apps:
            hint = QLabel('Add apps in Settings.')
            hint.setStyleSheet("color: #666; font-size: 11px; border: none; background: transparent;")
            self.other_apps_container.addWidget(hint)
            return

        for app in apps:
            btn = QPushButton(f'▹  {app["name"]}')
            btn.setStyleSheet("""
                QPushButton { text-align: left; background: transparent; color: #eee; border: none; padding: 6px 8px; border-radius: 6px; font-size: 12px; }
                QPushButton:hover { background: rgba(255,255,255,0.08); }
            """)
            btn.clicked.connect(lambda checked=False, p=app['path']: self._handle_launch(p))
            self.other_apps_container.addWidget(btn)

    def _handle_launch(self, path):
        self.on_launch_app(path)

    def _handle_system(self, action):
        self.on_system_action(action)

    def update_stats(self, memory_percent, cpu_percent):
        self.memory_bar.set_percent(memory_percent)
        self.cpu_bar.set_percent(cpu_percent)

    def refresh(self, config):
        self.config = config
        self._apply_theme()
        self._render_other_apps()


def run_system_action(action):
    commands = {
        'taskmanager': 'taskmgr',
        'controlpanel': 'control',
        'explorer': 'explorer.exe',
        'settings': 'start ms-settings:'
    }
    command = commands.get(action)
    if command:
        subprocess.Popen(command, shell=True)


class PopupMenu(QWidget):
    def __init__(self, config, on_save_settings, on_launch_app, on_preview_animation, on_closed=None):
        super().__init__()
        self.config = config
        self.on_save_settings = on_save_settings
        self.on_launch_app = on_launch_app
        self.on_preview_animation = on_preview_animation
        self.on_closed = on_closed

        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(WIDTH, HEIGHT)
        self._suppress_focus_out = False
        self._slide_anim = None
        self._boot_group = None
        self._fade_anim = None
        self._draw_in_group = None

        self.panel = RoundedPanel(config['accent_color'], config['background_color'], self)
        self.panel.setGeometry(0, 0, WIDTH, HEIGHT)

        self.content = QWidget(self.panel)
        self.content.setGeometry(0, 0, WIDTH, HEIGHT)
        self.opacity_effect = QGraphicsOpacityEffect(self.content)
        self.opacity_effect.setOpacity(1.0)
        self.content.setGraphicsEffect(self.opacity_effect)

        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()
        content_layout.addWidget(self.stack)

        self.main_page = MainPage(self.config, self._show_settings_page, self._handle_system_action, self._handle_launch_app)
        self.settings_page = SettingsPage(self.config, self._handle_settings_save, self._show_main_page, self.on_preview_animation)
        self.stack.addWidget(self.main_page)
        self.stack.addWidget(self.settings_page)

        self.boot_overlay = BootOverlay(config['accent_color'], config['background_color'], self.panel)
        self.boot_overlay.setGeometry(0, 0, WIDTH, HEIGHT)
        self.boot_overlay.hide()

        self.stats_timer = QTimer(self)
        self.stats_timer.timeout.connect(self._update_stats)
        psutil.cpu_percent(interval=None)

    def _handle_launch_app(self, path):
        self.on_launch_app(path)
        self.hide()

    def _handle_system_action(self, action):
        run_system_action(action)
        self.hide()

    def _show_settings_page(self):
        self.stack.setCurrentWidget(self.settings_page)

    def _show_main_page(self):
        self.stack.setCurrentWidget(self.main_page)

    def _handle_settings_save(self, new_config):
        self.on_save_settings(new_config)
        self.stack.setCurrentWidget(self.main_page)

    def _update_stats(self):
        memory_percent = psutil.virtual_memory().percent
        cpu_percent = psutil.cpu_percent(interval=None)
        self.main_page.update_stats(memory_percent, cpu_percent)

    def refresh(self, config):
        self.config = config
        self.panel.set_colors(config['accent_color'], config['background_color'])
        self.boot_overlay.set_colors(config['accent_color'], config['background_color'])
        self.main_page.refresh(config)
        self.settings_page.refresh_from_config(config)

    def _target_position(self):
        return compute_target_position(WIDTH, HEIGHT)

    def toggle(self):
        if self.isVisible():
            self.hide()
        else:
            self.stack.setCurrentWidget(self.main_page)
            self._show_with_slide()

    def show_settings(self):
        if self.isVisible():
            self._show_settings_page()
        else:
            self.stack.setCurrentWidget(self.settings_page)
            self._show_with_slide()

    def _show_with_slide(self):
        target = self._target_position()
        start = QPoint(target.x(), target.y() + SLIDE_DISTANCE)

        self.opacity_effect.setOpacity(0.0)
        self.boot_overlay.logo.set_circle_progress(0.0)
        self.boot_overlay.logo.set_m_progress(0.0)
        self.boot_overlay.logo.set_scale(1.0)
        self.main_page.mini_logo.set_circle_progress(0.0)
        self.main_page.mini_logo.set_m_progress(0.0)
        self.boot_overlay.show()
        self.boot_overlay.raise_()

        self.move(start)
        self.show()
        self.raise_()
        self.activateWindow()
        if self.windowHandle():
            self.windowHandle().requestActivate()

        self._suppress_focus_out = True
        QTimer.singleShot(250, self._enable_focus_out)
        self.stats_timer.start(1500)

        self._slide_anim = QPropertyAnimation(self, b'pos')
        self._slide_anim.setDuration(SLIDE_DURATION)
        self._slide_anim.setStartValue(start)
        self._slide_anim.setEndValue(target)
        self._slide_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._slide_anim.finished.connect(self._play_boot_sequence)
        self._slide_anim.start()

    def _play_boot_sequence(self):
        self._boot_group = build_boot_animation(self.boot_overlay.logo)
        self._boot_group.finished.connect(self._reveal_content)
        self._boot_group.start()

    def _reveal_content(self):
        self.boot_overlay.hide()
        self._fade_anim = QPropertyAnimation(self.opacity_effect, b'opacity')
        self._fade_anim.setDuration(CONTENT_FADE_DURATION)
        self._fade_anim.setStartValue(0.0)
        self._fade_anim.setEndValue(1.0)
        self._fade_anim.setEasingCurve(QEasingCurve.OutCubic)
        self._fade_anim.start()

        self._draw_in_group = build_draw_in_animation(self.main_page.mini_logo)
        self._draw_in_group.start()

    def _enable_focus_out(self):
        self._suppress_focus_out = False

    def focusOutEvent(self, event):
        if not self._suppress_focus_out:
            self.hide()
        super().focusOutEvent(event)

    def hideEvent(self, event):
        self.stats_timer.stop()
        super().hideEvent(event)
        if self.on_closed:
            self.on_closed()
