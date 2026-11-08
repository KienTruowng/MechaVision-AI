"""Thành phần hiển thị Dashboard V2; không chứa phép tính ước lượng."""
from PySide6.QtCore import Qt, QRectF, QSize
from PySide6.QtGui import QColor, QImage, QPainter, QPen, QFont
from PySide6.QtWidgets import (
    QWidget, QFrame, QLabel, QVBoxLayout, QHBoxLayout, QSizePolicy,
    QTableWidget, QAbstractItemView, QHeaderView,
)




def text_label(text, role=None, wrap=False):
    label = QLabel(text)
    if role:
        label.setObjectName(role)
    label.setWordWrap(wrap)
    return label


def badge(text, tone='data'):
    label = text_label(text, 'badge')
    label.setAlignment(Qt.AlignCenter)
    label.setSizePolicy(QSizePolicy.Maximum, QSizePolicy.Fixed)
    label.setMaximumHeight(28)
    set_tone(label, tone)
    return label


def set_tone(widget, tone):
    widget.setProperty('tone', tone)
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def panel(title, subtitle=None, trailing=None):
    frame = QFrame()
    frame.setObjectName('panel')
    layout = QVBoxLayout(frame)
    layout.setContentsMargins(14, 12, 14, 12)
    layout.setSpacing(9)
    heading = QHBoxLayout()
    heading.addWidget(text_label(title, 'panel_title'))
    heading.addStretch()
    if trailing is not None:
        heading.addWidget(trailing)
    layout.addLayout(heading)
    if subtitle:
        layout.addWidget(text_label(subtitle, 'muted', True))
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
        self.setObjectName('kpi')
        self.setMinimumWidth(130)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 10, 12, 10)
        layout.setSpacing(4)
        top = QHBoxLayout()
        top.addWidget(text_label(title, 'muted'))
        top.addStretch()
        top.addWidget(text_label(unit, 'eyebrow'))
        layout.addLayout(top)
        self.value = text_label('—', 'kpi_state' if state else 'kpi_value')
        self.value.setMinimumHeight(38 if not state else 28)
        self.value.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(self.value)
        layout.addWidget(text_label(caption, 'muted'))


class ImageSurface(QWidget):
    """Vẽ ảnh đúng tỷ lệ và tự vẽ lại khi đổi trang/kích thước, không có hoạt ảnh giả."""
    def __init__(self, title, detail):
        super().__init__()
        self.title = title
        self.detail = detail
        self.image = QImage()
        self.setMinimumSize(180, 150)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    @property
    def has_frame(self):
        return not self.image.isNull()

    def sizeHint(self):
        return QSize(480, 280)

    def set_frame(self, frame):
        height, width = frame.shape[:2]
        self.image = QImage(frame.data, width, height, frame.strides[0], QImage.Format_BGR888).copy()
        self.update()

    def clear(self):
        self.image = QImage()
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), QColor('#071321'))
        if self.has_frame:
            size = self.image.size().scaled(self.size(), Qt.KeepAspectRatio)
            rect = QRectF((self.width()-size.width())/2, (self.height()-size.height())/2,
                          size.width(), size.height())
            painter.setRenderHint(QPainter.SmoothPixmapTransform)
            painter.drawImage(rect, self.image)
        else:
            center = self.rect().center()
            painter.setPen(QPen(QColor('#28445e'), 1))
            painter.drawRoundedRect(QRectF(center.x()-22, center.y()-52, 44, 34), 6, 6)
            painter.drawEllipse(center.x()-8, center.y()-44, 16, 16)
            painter.setPen(QColor('#abc1d8'))
            painter.setFont(QFont(self.font().family(), 11, QFont.DemiBold))
            painter.drawText(QRectF(10, center.y()-4, self.width()-20, 25), Qt.AlignCenter, self.title)
            painter.setPen(QColor('#617b96'))
            painter.setFont(QFont(self.font().family(), 9))
            painter.drawText(QRectF(15, center.y()+24, self.width()-30, 40),
                             Qt.AlignHCenter | Qt.TextWordWrap, self.detail)
