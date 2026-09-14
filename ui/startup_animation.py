import sys

from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QSequentialAnimationGroup, QEasingCurve, Property, QRectF
from PySide6.QtGui import QPainter, QPainterPath, QColor, QPen
from PySide6.QtWidgets import QWidget, QApplication


class LogoWidget(QWidget):
    def __init__(self, accent_color, bg_color, parent=None, size=200):
        super().__init__(parent)
        self.accent_color = QColor(accent_color)
        self.bg_color = QColor(bg_color)
        self._circle_progress = 0.0
        self._m_progress = 0.0
        self._scale = 1.0
        self.setFixedSize(size, size)

    def get_circle_progress(self):
        return self._circle_progress

    def set_circle_progress(self, v):
        self._circle_progress = v
        self.update()

    circle_progress = Property(float, get_circle_progress, set_circle_progress)

    def get_m_progress(self):
        return self._m_progress

    def set_m_progress(self, v):
        self._m_progress = v
        self.update()

    m_progress = Property(float, get_m_progress, set_m_progress)

    def get_scale(self):
        return self._scale

    def set_scale(self, v):
        self._scale = v
        self.update()

    scale = Property(float, get_scale, set_scale)

    def _draw_logo(self, painter):
        cx, cy = self.width() / 2, self.height() / 2
        radius = min(self.width(), self.height()) * 0.275
        pen_width = max(3, int(min(self.width(), self.height()) * 0.035))

        pen = QPen(self.accent_color)
        pen.setWidth(pen_width)
        pen.setCapStyle(Qt.RoundCap)
        pen.setJoinStyle(Qt.RoundJoin)
        painter.setPen(pen)
        painter.setBrush(Qt.NoBrush)

        span = 360 * self._circle_progress
        rect = QRectF(cx - radius, cy - radius, radius * 2, radius * 2)
        painter.drawArc(rect, 90 * 16, -int(span * 16))

        if self._m_progress > 0:
            path = self._m_path(cx, cy, radius)
            partial = self._partial_path(path, self._m_progress)
            painter.strokePath(partial, pen)

    def _m_path(self, cx, cy, radius):
        path = QPainterPath()
        w = radius * 0.9
        h = radius * 0.9
        left = cx - w / 2
        right = cx + w / 2
        top = cy - h / 2
        bottom = cy + h / 2
        mid = cy + h / 8
        path.moveTo(left, bottom)
        path.lineTo(left, top)
        path.lineTo(cx, mid)
        path.lineTo(right, top)
        path.lineTo(right, bottom)
        return path

    def _partial_path(self, path, fraction):
        length = path.length()
        target_len = length * fraction
        partial = QPainterPath()
        steps = 120
        started = False
        for i in range(steps + 1):
            d = length * i / steps
            if d > target_len:
                break
            pt = path.pointAtPercent(path.percentAtLength(d))
            if not started:
                partial.moveTo(pt)
                started = True
            else:
                partial.lineTo(pt)
        return partial

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        cx, cy = self.width() / 2, self.height() / 2

        painter.save()
        painter.translate(cx, cy)
        painter.scale(self._scale, self._scale)
        painter.translate(-cx, -cy)
        self._draw_logo(painter)
        painter.restore()


def build_draw_in_animation(logo_widget):
    circle_anim = QPropertyAnimation(logo_widget, b'circle_progress')
    circle_anim.setDuration(450)
    circle_anim.setStartValue(0.0)
    circle_anim.setEndValue(1.0)
    circle_anim.setEasingCurve(QEasingCurve.OutCubic)

    m_anim = QPropertyAnimation(logo_widget, b'm_progress')
    m_anim.setDuration(350)
    m_anim.setStartValue(0.0)
    m_anim.setEndValue(1.0)
    m_anim.setEasingCurve(QEasingCurve.OutCubic)

    group = QSequentialAnimationGroup()
    group.addAnimation(circle_anim)
    group.addAnimation(m_anim)
    return group


def build_boot_animation(logo_widget):
    circle_anim = QPropertyAnimation(logo_widget, b'circle_progress')
    circle_anim.setDuration(600)
    circle_anim.setStartValue(0.0)
    circle_anim.setEndValue(1.0)
    circle_anim.setEasingCurve(QEasingCurve.OutCubic)

    m_anim = QPropertyAnimation(logo_widget, b'm_progress')
    m_anim.setDuration(450)
    m_anim.setStartValue(0.0)
    m_anim.setEndValue(1.0)
    m_anim.setEasingCurve(QEasingCurve.OutCubic)

    scale_up = QPropertyAnimation(logo_widget, b'scale')
    scale_up.setDuration(200)
    scale_up.setStartValue(1.0)
    scale_up.setEndValue(1.35)
    scale_up.setEasingCurve(QEasingCurve.OutQuad)

    scale_down = QPropertyAnimation(logo_widget, b'scale')
    scale_down.setDuration(380)
    scale_down.setStartValue(1.35)
    scale_down.setEndValue(1.0)
    scale_down.setEasingCurve(QEasingCurve.OutBack)

    m_reverse = QPropertyAnimation(logo_widget, b'm_progress')
    m_reverse.setDuration(350)
    m_reverse.setStartValue(1.0)
    m_reverse.setEndValue(0.0)
    m_reverse.setEasingCurve(QEasingCurve.InCubic)

    circle_reverse = QPropertyAnimation(logo_widget, b'circle_progress')
    circle_reverse.setDuration(450)
    circle_reverse.setStartValue(1.0)
    circle_reverse.setEndValue(0.0)
    circle_reverse.setEasingCurve(QEasingCurve.InCubic)

    group = QSequentialAnimationGroup()
    group.addAnimation(circle_anim)
    group.addAnimation(m_anim)
    group.addAnimation(scale_up)
    group.addAnimation(scale_down)
    group.addAnimation(m_reverse)
    group.addAnimation(circle_reverse)
    return group


class StartupAnimation(QWidget):
    def __init__(self, accent_color='#22c55e', bg_color='#0a0a0a', on_finished=None):
        super().__init__()
        self.on_finished = on_finished
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedSize(200, 200)

        self.logo = LogoWidget(accent_color, bg_color, self, size=200)
        self.logo.setGeometry(0, 0, 200, 200)

        screen_geo = QApplication.primaryScreen().geometry()
        self.move((screen_geo.width() - 200) // 2, (screen_geo.height() - 200) // 2)

        self.group = build_boot_animation(self.logo)
        self.group.finished.connect(self._on_finished_animating)

    def start(self):
        self.show()
        self.group.start()

    def _on_finished_animating(self):
        QTimer.singleShot(150, self._finish)

    def _finish(self):
        self.close()
        if self.on_finished:
            self.on_finished()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    anim = StartupAnimation()
    anim.start()
    sys.exit(app.exec())
