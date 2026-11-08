"""Khung ứng dụng và điều hướng; không sở hữu camera hoặc bộ ước lượng."""

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon, QPixmap, QPainter, QPen, QColor
from PySide6.QtWidgets import (
    QWidget,
    QFrame,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QStackedWidget,
    QButtonGroup,
)
from .dashboard_widgets import text_label, badge

PAGES = (
    ("Giám sát", "Quan sát cơ cấu và trạng thái ước lượng theo thời gian thực"),
    ("Phân tích", "Đối chiếu thị giác trực tiếp, EKF thời gian và EKF vật lý"),
    ("Thực nghiệm", "Đánh giá có thể tái lập trên cùng quan sát và tham chiếu độc lập"),
    ("Cài đặt", "Thiết lập nguồn thu nhận, bộ nhận diện và thông số phiên"),
)


def navigation_icon(index, selected=False):
    pixmap = QPixmap(22, 22)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setPen(QPen(QColor("#61d5ed" if selected else "#819ab4"), 1.5))
    if index == 0:
        painter.drawRoundedRect(2, 4, 18, 13, 3, 3)
        painter.drawLine(8, 20, 14, 20)
        painter.drawLine(11, 17, 11, 20)
    elif index == 1:
        painter.drawLine(3, 2, 3, 19)
        painter.drawLine(3, 19, 20, 19)
        for x1, y1, x2, y2 in [(5, 15, 9, 9), (9, 9, 14, 12), (14, 12, 19, 4)]:
            painter.drawLine(x1, y1, x2, y2)
    elif index == 2:
        painter.drawLine(8, 2, 14, 2)
        painter.drawLine(9, 2, 9, 8)
        painter.drawLine(13, 2, 13, 8)
        painter.drawLine(9, 8, 3, 19)
        painter.drawLine(13, 8, 19, 19)
        painter.drawLine(3, 19, 19, 19)
        painter.drawLine(6, 14, 16, 14)
    else:
        for y, x in [(5, 8), (11, 15), (17, 6)]:
            painter.drawLine(2, y, 20, y)
            painter.setBrush(QColor("#0a1625"))
            painter.drawEllipse(x - 2, y - 2, 4, 4)
    painter.end()
    return QIcon(pixmap)


class DashboardShell(QWidget):
    def __init__(self):
        super().__init__()
        self.setObjectName("shell")
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(176)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 23, 14, 18)
        side.setSpacing(8)
        brand = QHBoxLayout()
        mark = text_label("MV", "brand_icon")
        mark.setAlignment(Qt.AlignCenter)
        mark.setFixedSize(42, 42)
        brand.addWidget(mark)
        brand.addWidget(text_label("MECHA\nVISION", "brand"))
        side.addLayout(brand)
        side.addWidget(text_label("AI  /  DASHBOARD V2", "eyebrow"))
        side.addSpacing(29)
        side.addWidget(text_label("KHÔNG GIAN LÀM VIỆC", "eyebrow"))
        side.addSpacing(6)
        self.nav_group = QButtonGroup(self)
        self.nav_buttons = []
        for index, (title, subtitle) in enumerate(PAGES):
            button = QPushButton(title)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.setIcon(navigation_icon(index))
            button.setIconSize(QSize(20, 20))
            button.setMinimumHeight(45)
            button.setToolTip(subtitle)
            self.nav_group.addButton(button, index)
            self.nav_buttons.append(button)
            side.addWidget(button)
        side.addStretch()
        side.addWidget(text_label("THỊ GIÁC × ĐỘNG HỌC", "eyebrow"))
        side.addWidget(
            text_label(
                "Nền tảng nghiên cứu\nƯớc lượng có ràng buộc vật lý", "muted", True
            )
        )
        side.addSpacing(10)
        self.sidebar_status = badge("CHƯA CÓ PHIÊN", "muted")
        side.addWidget(self.sidebar_status)
        outer.addWidget(sidebar)

        main = QVBoxLayout()
        main.setContentsMargins(20, 15, 20, 12)
        main.setSpacing(12)
        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(text_label("MECHAVISION AI  /  TRẠM NGHIÊN CỨU", "eyebrow"))
        self.page_title = text_label("Giám sát", "page_title")
        titles.addWidget(self.page_title)
        top.addLayout(titles)
        top.addStretch()
        self.source_badge = badge("MÔ PHỎNG", "warning")
        self.system_badge = badge("SẴN SÀNG", "muted")
        self.source_badge.setMinimumWidth(150)
        self.system_badge.setMinimumWidth(116)
        top.addWidget(self.source_badge)
        top.addWidget(self.system_badge)
        self.configure_btn = QPushButton("Cấu hình")
        self.start_btn = QPushButton("Bắt đầu phiên")
        self.start_btn.setObjectName("primary")
        self.stop_btn = QPushButton("Dừng")
        self.stop_btn.setObjectName("danger")
        self.stop_btn.setEnabled(False)
        for button in (self.configure_btn, self.start_btn, self.stop_btn):
            top.addWidget(button)
        main.addLayout(top)
        self.stack = QStackedWidget()
        main.addWidget(self.stack, 1)
        footer = QHBoxLayout()
        self.session_text = text_label(
            "Chưa có phiên • Dữ liệu được ghi khi bắt đầu", "muted"
        )
        self.session_text.setWordWrap(True)
        footer.addWidget(self.session_text, 1)
        footer.addWidget(
            text_label("Nguyên mẫu nghiên cứu • Không chẩn đoán hư hỏng", "muted")
        )
        main.addLayout(footer)
        outer.addLayout(main, 1)

    def select_page(self, index):
        self.stack.setCurrentIndex(index)
        self.page_title.setText(PAGES[index][0])
        for number, button in enumerate(self.nav_buttons):
            button.setChecked(number == index)
            button.setIcon(navigation_icon(number, number == index))
