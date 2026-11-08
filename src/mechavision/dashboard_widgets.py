"""Thành phần hiển thị Dashboard V2; không chứa phép tính ước lượng."""

import math
from PySide6.QtCore import Qt, QRectF, QSize, QPointF
from PySide6.QtGui import QColor, QImage, QPainter, QPainterPath, QPen, QFont
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QSizePolicy,
    QTableWidget,
    QAbstractItemView,
    QHeaderView,
)


def text_label(text, role=None, wrap=False):
    label = QLabel(text)
    if role:
        label.setObjectName(role)
    label.setWordWrap(wrap)
    return label


def badge(text, tone="data"):
    label = text_label(text, "badge")
    label.setAlignment(Qt.AlignCenter)
    label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    label.setMaximumHeight(28)
    set_tone(label, tone)
    return label


def set_tone(widget, tone):
    widget.setProperty("tone", tone)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def panel(title, subtitle=None, trailing=None):
    frame = QFrame()
    frame.setObjectName("panel")
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(9)
    heading = QHBoxLayout()
    heading.addWidget(text_label(title, "panel_title"))
    heading.addStretch()
    if trailing is not None:
        heading.addWidget(trailing)
    layout.addLayout(heading)
    if subtitle:
        layout.addWidget(text_label(subtitle, "muted", True))
    return frame, layout


def table(headers):
    widget = QTableWidget(0, len(headers))
    widget.setHorizontalHeaderLabels(headers)
    widget.verticalHeader().hide()
    widget.setEditTriggers(QAbstractItemView.NoEditTriggers)
    widget.setSelectionBehavior(QAbstractItemView.SelectRows)
    widget.setAlternatingRowColors(True)
    widget.setShowGrid(False)
    widget.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
    widget.verticalHeader().setDefaultSectionSize(32)
    widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    return widget


class KpiCard(QFrame):
    def __init__(self, title, unit, caption, state=False):
        super().__init__()
        self.setObjectName("kpi")
        self.setMinimumWidth(138)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        top = QHBoxLayout()
        top.addWidget(text_label(title, "muted"))
        top.addStretch()
        layout.addLayout(top)
        self.value = text_label("—", "kpi_state" if state else "kpi_value")
        self.value.setMinimumHeight(44 if not state else 32)
        self.value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        value_row = QHBoxLayout()
        value_row.setSpacing(4)
        value_row.addWidget(self.value)
        value_row.addStretch()
        value_row.addWidget(text_label(unit, "unit"), 0, Qt.AlignBottom)
        layout.addLayout(value_row)
        self.sparkline = Sparkline()
        if state:
            self.sparkline.hide()
        else:
            layout.addWidget(self.sparkline)
        self.caption = text_label(caption, "micro")
        layout.addWidget(self.caption)


class Sparkline(QWidget):
    """Xu hướng chỉ từ mẫu đã nhận; giữ khoảng trống khi thiếu dữ liệu."""

    def __init__(self, color="#56d8e6"):
        super().__init__()
        self.values = []
        self.color = QColor(color)
        self.setFixedHeight(20)
        self.setMinimumWidth(20)
        self.setToolTip("Tối đa 90 mẫu gần nhất của phiên hiện tại; giữ khoảng trống dữ liệu")

    def set_values(self, values):
        self.values = list(values)[-90:]
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        finite = [v for v in self.values if math.isfinite(v)]
        if len(finite) < 2:
            return
        low, high = min(finite), max(finite)
        span = high - low
        path = QPainterPath()
        connected = False
        for index, value in enumerate(self.values):
            if not math.isfinite(value):
                connected = False
                continue
            x = 1 + index * (self.width() - 2) / max(1, len(self.values) - 1)
            y = self.height() / 2 if span == 0 else 2 + (high - value) / span * (self.height() - 4)
            if connected:
                path.lineTo(x, y)
            else:
                path.moveTo(x, y)
            connected = True
        painter.setPen(QPen(self.color, 1.4))
        painter.drawPath(path)


class BrandMark(QWidget):
    """Biểu trưng riêng: trục quay và liên kết cơ khí trong ô kỹ thuật."""

    def __init__(self):
        super().__init__()
        self.setFixedSize(42, 42)

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        p.setPen(QPen(QColor("#235263"), 1))
        p.setBrush(QColor("#102d38"))
        p.drawRoundedRect(QRectF(1, 1, 40, 40), 9, 9)
        p.setPen(QPen(QColor("#43b5f4"), 3))
        p.drawLine(11, 28, 18, 13)
        p.setPen(QPen(QColor("#5ee2d0"), 3))
        p.drawLine(18, 13, 32, 26)
        p.setPen(QPen(QColor("#d7eef5"), 1.5))
        p.setBrush(QColor("#102d38"))
        for x, y in [(11, 28), (18, 13), (32, 26)]:
            p.drawEllipse(QPointF(x, y), 3, 3)


class ImageSurface(QWidget):
    """Vẽ ảnh đúng tỷ lệ và tự vẽ lại khi đổi trang/kích thước, không có hoạt ảnh giả."""

    def __init__(self, title, detail):
        super().__init__()
        self.title = title
        self.detail = detail
        self.image = QImage()
        self.focus_rect = None
        self.zoom_factor = 1.0
        self.setMinimumSize(180, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    @property
    def has_frame(self):
        return not self.image.isNull()

    def sizeHint(self):
        return QSize(480, 280)

    def set_frame(self, frame):
        height, width = frame.shape[:2]
        self.image = QImage(
            frame.data, width, height, frame.strides[0], QImage.Format_BGR888
        ).copy()
        self.update()

    def clear(self):
        self.image = QImage()
        self.update()

    def set_focus_rect(self, rect):
        """Cận cảnh chỉ khi vẽ; ảnh gốc và tọa độ nhận diện giữ nguyên."""
        self.focus_rect = rect
        self.update()

    def set_zoom(self, factor):
        self.zoom_factor = max(1.0, min(2.0, float(factor)))
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor("#071321"))
        if self.has_frame:
            source = QRectF(self.image.rect())
            if self.focus_rect is not None:
                clipped = source.intersected(self.focus_rect)
                if not clipped.isEmpty():
                    source = clipped
            if self.zoom_factor > 1:
                center = source.center()
                source.setSize(source.size() / self.zoom_factor)
                source.moveCenter(center)
            size = source.size().scaled(self.size(), Qt.KeepAspectRatio)
            rect = QRectF(
                (self.width() - size.width()) / 2,
                (self.height() - size.height()) / 2,
                size.width(),
                size.height(),
            )
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawImage(rect, self.image, source)
        else:
            center = self.rect().center()
            painter.setPen(QPen(QColor("#28445e"), 1))
            painter.drawRoundedRect(
                QRectF(center.x() - 22, center.y() - 52, 44, 34), 6, 6
            )
            painter.drawEllipse(center.x() - 8, center.y() - 44, 16, 16)
            painter.setPen(QColor("#abc1d8"))
            painter.setFont(QFont(self.font().family(), 11, QFont.DemiBold))
            painter.drawText(
                QRectF(10, center.y() - 4, self.width() - 20, 25),
                Qt.AlignCenter,
                self.title,
            )
            painter.setPen(QColor("#617b96"))
            painter.setFont(QFont(self.font().family(), 9))
            painter.drawText(
                QRectF(15, center.y() + 24, self.width() - 30, 40),
                Qt.AlignHCenter | Qt.TextWordWrap,
                self.detail,
            )


class TwinSurface(ImageSurface):
    """Vẽ lại đúng kích thước viewport từ cùng ước lượng, không tự chạy thời gian."""

    def __init__(self, title, detail):
        super().__init__(title, detail)
        self._geometry = None
        self.estimate = None

    def set_estimate(self, geometry, estimate):
        self._geometry, self.estimate = geometry, estimate
        self._render()

    def _render(self):
        if self._geometry is not None and self.estimate is not None:
            from .render import twin_frame

            self.set_frame(twin_frame(self._geometry, self.estimate,
                                      max(180, self.width()), max(150, self.height())))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()

    def clear(self):
        self._geometry = self.estimate = None
        super().clear()
