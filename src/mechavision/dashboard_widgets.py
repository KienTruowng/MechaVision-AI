"""Thành phần hiển thị Dashboard V2; không chứa phép tính ước lượng."""

import math
from PySide6.QtCore import Qt, QRectF, QSize, QPointF
from PySide6.QtGui import (
    QColor,
    QImage,
    QPainter,
    QPainterPath,
    QPen,
    QFont,
    QIcon,
    QPixmap,
)
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


def viewport_icon(kind):
    """Biểu tượng vector đồng bộ cho các thao tác vùng nhìn."""
    pixmap = QPixmap(20, 20)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#A9DDEA"), 1.6))
    if kind == "fit":
        for x, y, dx, dy in [
            (3, 3, 1, 1),
            (17, 3, -1, 1),
            (3, 17, 1, -1),
            (17, 17, -1, -1),
        ]:
            painter.drawLine(x, y, x + dx * 5, y)
            painter.drawLine(x, y, x, y + dy * 5)
    elif kind == "focus":
        painter.drawEllipse(4, 4, 12, 12)
        painter.drawLine(10, 1, 10, 6)
        painter.drawLine(10, 14, 10, 19)
        painter.drawLine(1, 10, 6, 10)
        painter.drawLine(14, 10, 19, 10)
    else:
        painter.drawLine(4, 15, 9, 5)
        painter.drawLine(9, 5, 16, 12)
        painter.setBrush(QColor("#101B2B"))
        for x, y in [(4, 15), (9, 5), (16, 12)]:
            painter.drawEllipse(QPointF(x, y), 2.5, 2.5)
    painter.end()
    return QIcon(pixmap)


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
    def __init__(self, title, unit, caption, state=False, compact=False):
        super().__init__()
        self.setObjectName("kpi")
        self.setMinimumWidth(138)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        top = QHBoxLayout()
        self.title_label = text_label(title, "muted")
        top.addWidget(self.title_label)
        top.addStretch()
        layout.addLayout(top)
        self.value = text_label("—", "kpi_state" if state else "kpi_value")
        self.value.setMinimumHeight(44 if not state else 32)
        self.value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        value_row = QHBoxLayout()
        value_row.setSpacing(4)
        value_row.addWidget(self.value)
        value_row.addStretch()
        self.unit_label = text_label(unit, "unit")
        value_row.addWidget(self.unit_label, 0, Qt.AlignBottom)
        layout.addLayout(value_row)
        self.sparkline = Sparkline()
        if state:
            self.sparkline.hide()
        else:
            layout.addWidget(self.sparkline)
        self.caption = text_label(caption, "micro")
        layout.addWidget(self.caption)
        self.caption.hide()
        self.setToolTip(caption)
        layout.setContentsMargins(12, 7, 12, 7)
        layout.setSpacing(2)
        self.sparkline.setFixedHeight(14)
        if compact:
            self.setObjectName("metric_cell")
            self.setMinimumWidth(96)
            self.value.setMinimumHeight(40)
            self.value.setStyleSheet("font-size:30px; font-weight:600;")
            self.title_label.setText(title + (" · " + unit if unit else ""))
            self.unit_label.hide()
            self.sparkline.hide()
            layout.setContentsMargins(6, 4, 6, 4)


class Sparkline(QWidget):
    """Xu hướng chỉ từ mẫu đã nhận; giữ khoảng trống khi thiếu dữ liệu."""

    def __init__(self, color="#56d8e6"):
        super().__init__()
        self.values = []
        self.color = QColor(color)
        self.setFixedHeight(20)
        self.setMinimumWidth(20)
        self.setToolTip(
            "Tối đa 90 mẫu gần nhất của phiên hiện tại; giữ khoảng trống dữ liệu"
        )

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
            y = (
                self.height() / 2
                if span == 0
                else 2 + (high - value) / span * (self.height() - 4)
            )
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
        self.pan_offset = QPointF()
        self._drag_position = None
        self.observation = None
        self.source_caption = ""
        self.show_annotations = True
        self._image_rect = QRectF()
        self._source_rect = QRectF()
        self.setCursor(Qt.OpenHandCursor)
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
        self.observation = None
        self.fit_view()
        self.update()

    def set_overlay(self, observation):
        self.observation = observation
        self.update()

    def fit_view(self):
        self.zoom_factor = 1.0
        self.pan_offset = QPointF()
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.has_frame:
            self._drag_position = event.position()
            self.setCursor(Qt.ClosedHandCursor)

    def mouseMoveEvent(self, event):
        if self._drag_position is not None and self._image_rect.width() > 0:
            delta = event.position() - self._drag_position
            self.pan_offset -= delta * (
                self._source_rect.width() / self._image_rect.width()
            )
            self._drag_position = event.position()
            self.update()

    def mouseReleaseEvent(self, event):
        self._drag_position = None
        self.setCursor(Qt.OpenHandCursor)

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
            source.translate(self.pan_offset)
            # Giới hạn pan vào ảnh nguồn; không thay tọa độ quan sát.
            source.moveLeft(
                max(0, min(source.left(), self.image.width() - source.width()))
            )
            source.moveTop(
                max(0, min(source.top(), self.image.height() - source.height()))
            )
            size = source.size().scaled(self.size(), Qt.KeepAspectRatio)
            rect = QRectF(
                (self.width() - size.width()) / 2,
                (self.height() - size.height()) / 2,
                size.width(),
                size.height(),
            )
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawImage(rect, self.image, source)
            self._image_rect, self._source_rect = rect, source
            if self.show_annotations and self.observation is not None:
                self._draw_overlay(painter, rect, source)
            if self.source_caption:
                font = QFont(self.font().family())
                font.setPixelSize(12)
                font.setWeight(QFont.DemiBold)
                painter.setFont(font)
                caption = self.source_caption
                label = QRectF(
                    14, 14, painter.fontMetrics().horizontalAdvance(caption) + 20, 28
                )
                painter.setPen(QPen(QColor("#68532f"), 1))
                painter.setBrush(QColor(28, 27, 25, 240))
                painter.drawRoundedRect(label, 4, 4)
                painter.setPen(QColor("#F1BE62"))
                painter.drawText(label, Qt.AlignCenter, caption)
                painter.setPen(QColor("#AABCD1"))
                painter.drawText(
                    QRectF(self.width() - 156, 17, 142, 24),
                    Qt.AlignRight,
                    f"{self.image.width()} × {self.image.height()} px",
                )
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

    def _draw_overlay(self, painter, rect, source):
        painter.save()
        painter.setClipRect(rect)
        factor = rect.width() / source.width()
        positions = {
            name: QPointF(
                rect.x() + (point.x - source.x()) * factor,
                rect.y() + (point.y - source.y()) * factor,
            )
            for name, point in self.observation.landmarks.items()
        }
        colors = {"pivot": "#d8e8f5", "crank": "#55d9ef", "piston": "#ad96ff"}
        titles = {"pivot": "Tâm quay", "crank": "Chốt khuỷu", "piston": "Khớp pít-tông"}
        painter.setPen(QPen(QColor("#60dcec"), 2))
        for a, b in [("pivot", "crank"), ("crank", "piston")]:
            if a in positions and b in positions:
                painter.drawLine(positions[a], positions[b])
        font = QFont(self.font().family())
        font.setPixelSize(13)
        font.setWeight(QFont.DemiBold)
        painter.setFont(font)
        placed = []
        for name, point in positions.items():
            color = QColor(colors.get(name, "#ffffff"))
            painter.setPen(QPen(color, 2))
            painter.setBrush(QColor("#071321"))
            painter.drawEllipse(point, 6, 6)
            painter.setBrush(color)
            painter.drawEllipse(point, 2, 2)
            text = f"{titles.get(name, name)}  {self.observation.landmarks[name].confidence:.2f}"
            width = painter.fontMetrics().horizontalAdvance(text) + 16
            candidates = []
            for dx, dy in [
                (16, -50),
                (16, 28),
                (-width - 16, -50),
                (-width - 16, 28),
                (16, -78),
            ]:
                box = QRectF(
                    max(rect.left() + 5, min(point.x() + dx, rect.right() - width - 5)),
                    max(rect.top() + 5, min(point.y() + dy, rect.bottom() - 28)),
                    width,
                    24,
                )
                penalty = 20 * sum(box.intersects(other) for other in placed)
                penalty += 20 * sum(
                    box.adjusted(-8, -8, 8, 8).contains(p) for p in positions.values()
                )
                for a, b in [("pivot", "crank"), ("crank", "piston")]:
                    if a in positions and b in positions:
                        penalty += sum(
                            box.contains(
                                positions[a]
                                + (positions[b] - positions[a]) * (step / 12)
                            )
                            for step in range(13)
                        )
                candidates.append((penalty, box))
            box = min(candidates, key=lambda item: item[0])[1]
            placed.append(box)
            anchor = QPointF(
                max(box.left(), min(point.x(), box.right())),
                max(box.top(), min(point.y(), box.bottom())),
            )
            painter.setPen(QPen(QColor("#617A91"), 1))
            painter.drawLine(point, anchor)
            painter.setPen(QPen(QColor("#2d485d"), 1))
            painter.setBrush(QColor(10, 24, 38, 238))
            painter.drawRoundedRect(box, 4, 4)
            painter.setPen(color)
            painter.drawText(box, Qt.AlignCenter, text)
        painter.restore()


class TwinSurface(ImageSurface):
    """Vẽ lại đúng kích thước viewport từ cùng ước lượng, không tự chạy thời gian."""

    def __init__(self, title, detail):
        super().__init__(title, detail)
        self._geometry = None
        self.estimate = None

    def set_estimate(self, geometry, estimate):
        self._geometry, self.estimate = geometry, estimate
        if self.isVisible():
            self._render()

    def showEvent(self, event):
        super().showEvent(event)
        self._render()

    def _render(self):
        if self._geometry is not None and self.estimate is not None:
            from .render import twin_frame

            self.set_frame(
                twin_frame(
                    self._geometry,
                    self.estimate,
                    max(180, self.width()),
                    max(150, self.height()),
                )
            )

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._render()

    def clear(self):
        self._geometry = self.estimate = None
        super().clear()
