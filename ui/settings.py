import os

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QColorDialog, QFileDialog, QListWidget, QListWidgetItem, QCheckBox, QScrollArea,
    QGraphicsDropShadowEffect
)


def _readable_text_color(hex_color):
    color = QColor(hex_color)
    luminance = (0.299 * color.red() + 0.587 * color.green() + 0.114 * color.blue()) / 255
    return '#000000' if luminance > 0.55 else '#ffffff'


class SettingsPage(QWidget):
    def __init__(self, config, on_save, on_back, on_preview_animation):
        super().__init__()
        self.config = dict(config)
        self.config['apps'] = list(config.get('apps', []))
        self.on_save = on_save
        self.on_back = on_back
        self.on_preview_animation = on_preview_animation

        outer = QVBoxLayout(self)
        outer.setContentsMargins(18, 16, 18, 16)
        outer.setSpacing(8)

        header = QHBoxLayout()
        back_btn = QPushButton('←')
        back_btn.setFixedSize(26, 26)
        back_btn.setStyleSheet("QPushButton { background: transparent; color: #ccc; border: none; font-size: 15px; } QPushButton:hover { color: white; }")
        back_btn.clicked.connect(self._handle_back)
        header.addWidget(back_btn)
        title = QLabel('Settings')
        title.setStyleSheet('font-size: 14px; font-weight: 600; color: #eee; margin-left: 4px;')
        header.addWidget(title)
        header.addStretch()
        outer.addLayout(header)
        self.back_btn = back_btn

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; } QScrollBar:vertical { width: 6px; background: transparent; } QScrollBar::handle:vertical { background: rgba(255,255,255,0.15); border-radius: 3px; }")

        scroll_body = QWidget()
        scroll_body.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(scroll_body)
        layout.setContentsMargins(0, 0, 6, 0)
        layout.setSpacing(10)

        layout.addWidget(self._section_label('Hotkey'))
        self.hotkey_input = QLineEdit(self.config['hotkey'])
        self.hotkey_input.setReadOnly(True)
        self.hotkey_input.installEventFilter(self)
        self.hotkey_input.setStyleSheet(self._input_style())
        layout.addWidget(self.hotkey_input)

        layout.addWidget(self._section_label('Colors'))
        color_row = QHBoxLayout()
        color_row.setSpacing(6)
        self.accent_btn = QPushButton('Accent')
        self.accent_btn.setStyleSheet(self._color_btn_style(self.config['accent_color']))
        self.accent_btn.clicked.connect(self._pick_accent)
        self._apply_swatch_glow(self.accent_btn, self.config['accent_color'])
        self.bg_btn = QPushButton('Background')
        self.bg_btn.setStyleSheet(self._color_btn_style(self.config['background_color']))
        self.bg_btn.clicked.connect(self._pick_background)
        color_row.addWidget(self.accent_btn)
        color_row.addWidget(self.bg_btn)
        layout.addLayout(color_row)

        preview_btn = QPushButton('Preview Startup Animation')
        preview_btn.setStyleSheet(self._plain_btn_style())
        preview_btn.clicked.connect(self._preview)
        layout.addWidget(preview_btn)
        self.preview_btn = preview_btn

        layout.addWidget(self._section_label('Performance'))
        self.performance_checkbox = QCheckBox('PC Performance Mode')
        self.performance_checkbox.setChecked(self.config.get('performance_mode', False))
        self.performance_checkbox.setStyleSheet(self._checkbox_style())
        self.performance_checkbox.stateChanged.connect(self._toggle_performance_mode)
        layout.addWidget(self.performance_checkbox)
        perf_hint = QLabel('Unloads the menu when closed, reloads it on open. Lighter on your PC.')
        perf_hint.setWordWrap(True)
        perf_hint.setStyleSheet('color: #777; font-size: 10px;')
        layout.addWidget(perf_hint)

        self.autostart_checkbox = QCheckBox('Start with Windows')
        self.autostart_checkbox.setChecked(self.config.get('start_with_windows', False))
        self.autostart_checkbox.setStyleSheet(self._checkbox_style())
        self.autostart_checkbox.stateChanged.connect(self._toggle_autostart)
        layout.addWidget(self.autostart_checkbox)

        layout.addWidget(self._section_label('Other Apps'))
        self.apps_list = QListWidget()
        self.apps_list.setFixedHeight(100)
        self.apps_list.setStyleSheet("background: rgba(255,255,255,0.05); border: 1px solid #333; border-radius: 6px; font-size: 12px; color: #eee;")
        layout.addWidget(self.apps_list)
        self._refresh_apps_list()

        app_buttons = QHBoxLayout()
        app_buttons.setSpacing(6)
        add_btn = QPushButton('+ Add')
        add_btn.setStyleSheet(self._plain_btn_style())
        add_btn.clicked.connect(self._add_app)
        remove_btn = QPushButton('Remove')
        remove_btn.setStyleSheet(self._plain_btn_style())
        remove_btn.clicked.connect(self._remove_app)
        app_buttons.addWidget(add_btn)
        app_buttons.addWidget(remove_btn)
        layout.addLayout(app_buttons)
        self.add_btn = add_btn
        self.remove_btn = remove_btn

        layout.addStretch()
        scroll.setWidget(scroll_body)
        outer.addWidget(scroll, 1)

        self.save_btn = QPushButton('Save')
        self.save_btn.setStyleSheet(self._save_btn_style())
        self.save_btn.clicked.connect(self._save)
        self._apply_swatch_glow(self.save_btn, self.config['accent_color'])
        outer.addWidget(self.save_btn)

    def _section_label(self, text):
        label = QLabel(text.upper())
        label.setStyleSheet('color: #888; font-size: 10px; letter-spacing: 1px; margin-top: 4px;')
        return label

    def _input_style(self):
        return "background: rgba(255,255,255,0.05); border: 1px solid #333; border-radius: 6px; color: #eee; padding: 6px; font-size: 12px;"

    def _plain_btn_style(self):
        return """
            QPushButton {
                background: rgba(255,255,255,0.06);
                color: #eee;
                border: 1px solid rgba(255,255,255,0.08);
                border-radius: 6px;
                padding: 8px 10px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: rgba(255,255,255,0.14);
            }
        """

    def _color_btn_style(self, color):
        text_color = _readable_text_color(color)
        return f"background: {color}; color: {text_color}; border: 1px solid rgba(255,255,255,0.2); padding: 8px; border-radius: 6px; font-weight: 600; font-size: 12px;"

    def _save_btn_style(self):
        text_color = _readable_text_color(self.config['accent_color'])
        return f"background: {self.config['accent_color']}; color: {text_color}; font-weight: 600; padding: 9px; border-radius: 8px; font-size: 13px;"

    def _apply_swatch_glow(self, widget, color):
        glow = QGraphicsDropShadowEffect()
        glow.setBlurRadius(18)
        glow.setOffset(0, 2)
        glow.setColor(QColor(color))
        widget.setGraphicsEffect(glow)

    def _checkbox_style(self):
        accent = self.config.get('accent_color', '#22c55e')
        return f"""
            QCheckBox {{ color: #eee; font-size: 12px; spacing: 8px; }}
            QCheckBox::indicator {{
                width: 16px; height: 16px;
                border: 1px solid rgba(255,255,255,0.3);
                border-radius: 4px;
                background: rgba(255,255,255,0.05);
            }}
            QCheckBox::indicator:checked {{
                background: {accent};
                border: 1px solid {accent};
            }}
        """

    def _pick_accent(self):
        color = QColorDialog.getColor(QColor(self.config['accent_color']), self, 'Pick Accent Color')
        if color.isValid():
            self.config['accent_color'] = color.name()
            self.accent_btn.setStyleSheet(self._color_btn_style(color.name()))
            self._apply_swatch_glow(self.accent_btn, color.name())
            self.save_btn.setStyleSheet(self._save_btn_style())
            self._apply_swatch_glow(self.save_btn, color.name())
            self.performance_checkbox.setStyleSheet(self._checkbox_style())
            self.autostart_checkbox.setStyleSheet(self._checkbox_style())

    def _pick_background(self):
        color = QColorDialog.getColor(QColor(self.config['background_color']), self, 'Pick Background Color')
        if color.isValid():
            self.config['background_color'] = color.name()
            self.bg_btn.setStyleSheet(self._color_btn_style(color.name()))

    def _preview(self):
        self.on_preview_animation(self.config['accent_color'], self.config['background_color'])

    def _toggle_performance_mode(self, state):
        self.config['performance_mode'] = bool(state)

    def _toggle_autostart(self, state):
        self.config['start_with_windows'] = bool(state)

    def _refresh_apps_list(self):
        self.apps_list.clear()
        for app in self.config.get('apps', []):
            self.apps_list.addItem(QListWidgetItem(app['name']))

    def _add_app(self):
        path, _ = QFileDialog.getOpenFileName(self, 'Select an application', '', 'Executables (*.exe *.lnk *.bat)')
        if not path:
            return
        name = os.path.splitext(os.path.basename(path))[0]
        self.config.setdefault('apps', []).append({'name': name, 'path': path})
        self._refresh_apps_list()

    def _remove_app(self):
        row = self.apps_list.currentRow()
        if row >= 0:
            del self.config['apps'][row]
            self._refresh_apps_list()

    def eventFilter(self, obj, event):
        if obj is self.hotkey_input and event.type() == event.Type.KeyPress:
            self._capture_hotkey(event)
            return True
        return super().eventFilter(obj, event)

    def _capture_hotkey(self, event):
        parts = []
        modifiers = event.modifiers()
        if modifiers & Qt.ControlModifier:
            parts.append('ctrl')
        if modifiers & Qt.AltModifier:
            parts.append('alt')
        if modifiers & Qt.ShiftModifier:
            parts.append('shift')
        if modifiers & Qt.MetaModifier:
            parts.append('windows')

        key = event.key()
        if key in (Qt.Key_Control, Qt.Key_Alt, Qt.Key_Shift, Qt.Key_Meta):
            return

        key_text = event.text().strip()
        key_name = key_text.lower() if key_text else self._special_key_name(key)
        if not key_name:
            return

        parts.append(key_name)
        accelerator = '+'.join(parts)
        self.hotkey_input.setText(accelerator)
        self.config['hotkey'] = accelerator

    def _special_key_name(self, key):
        mapping = {
            Qt.Key_Space: 'space',
            Qt.Key_Tab: 'tab',
            Qt.Key_Escape: 'esc',
            Qt.Key_F1: 'f1', Qt.Key_F2: 'f2', Qt.Key_F3: 'f3', Qt.Key_F4: 'f4',
            Qt.Key_F5: 'f5', Qt.Key_F6: 'f6', Qt.Key_F7: 'f7', Qt.Key_F8: 'f8',
            Qt.Key_F9: 'f9', Qt.Key_F10: 'f10', Qt.Key_F11: 'f11', Qt.Key_F12: 'f12',
        }
        return mapping.get(key)

    def refresh_from_config(self, config):
        self.config = dict(config)
        self.config['apps'] = list(config.get('apps', []))
        self.hotkey_input.setText(self.config['hotkey'])
        self.accent_btn.setStyleSheet(self._color_btn_style(self.config['accent_color']))
        self._apply_swatch_glow(self.accent_btn, self.config['accent_color'])
        self.bg_btn.setStyleSheet(self._color_btn_style(self.config['background_color']))
        self.save_btn.setStyleSheet(self._save_btn_style())
        self._apply_swatch_glow(self.save_btn, self.config['accent_color'])
        self.performance_checkbox.setStyleSheet(self._checkbox_style())
        self.autostart_checkbox.setStyleSheet(self._checkbox_style())
        self.performance_checkbox.setChecked(self.config.get('performance_mode', False))
        self.autostart_checkbox.setChecked(self.config.get('start_with_windows', False))
        self._refresh_apps_list()

    def _handle_back(self):
        self.on_back()

    def _save(self):
        self.on_save(self.config)
