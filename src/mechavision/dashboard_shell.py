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
from .dashboard_widgets import text_label, badge, BrandMark, panel

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
        sidebar.setFixedWidth(196)
        side = QVBoxLayout(sidebar)
        side.setContentsMargins(14, 23, 14, 18)
        side.setSpacing(8)
        brand = QHBoxLayout()
        mark = BrandMark()
        brand.addWidget(mark)
        brand.addWidget(text_label("MECHA\nVISION", "brand"))
        side.addLayout(brand)
        side.addWidget(text_label("NỀN TẢNG NGHIÊN CỨU · V3", "eyebrow"))
        side.addSpacing(20)
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
        session, session_layout = panel("TRẠM NGHIÊN CỨU")
        self.sidebar_source = text_label("Chưa có dữ liệu", "muted", True)
        session_layout.addWidget(self.sidebar_source)
        self.sidebar_frames = text_label("— khung hình", "session_value")
        session_layout.addWidget(self.sidebar_frames)
        self.sidebar_time = text_label("Chưa có thời gian phiên", "micro", True)
        session_layout.addWidget(self.sidebar_time)
        self.sidebar_status = badge("CHƯA CÓ PHIÊN", "muted")
        session_layout.addWidget(self.sidebar_status)
        side.addWidget(session)
        side.addSpacing(8)
        side.addWidget(text_label("THỊ GIÁC × ĐỘNG HỌC", "eyebrow"))
        side.addWidget(text_label("Mô phỏng không thay thế kiểm chứng trên cơ cấu thật.", "micro", True))
        outer.addWidget(sidebar)

        main = QVBoxLayout()
        main.setContentsMargins(20, 15, 20, 12)
        main.setSpacing(12)
        top = QHBoxLayout()
        titles = QVBoxLayout()
        titles.setSpacing(3)
        titles.addWidget(text_label("MECHAVISION AI  /  TRẠM NGHIÊN CỨU V3", "eyebrow"))
        self.page_title = text_label("Giám sát", "page_title")
        titles.addWidget(self.page_title)
        top.addLayout(titles)
        top.addStretch()
        self.source_badge = badge("MÔ PHỎNG", "warning")
        self.system_badge = badge("SẴN SÀNG", "muted")
        self.source_badge.setMinimumWidth(150)
        self.system_badge.setMinimumWidth(132)
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

    def update_session(self, state):
        from .dashboard_monitoring import SOURCE_LABELS

        if state.sample_count or state.phase != "idle":
            self.sidebar_source.setText(SOURCE_LABELS[state.mode])
        self.sidebar_frames.setText(f"{state.sample_count:,} khung hình" if state.sample_count else "— khung hình")
        times = state.series["time"]
        self.sidebar_time.setText(f"Cửa sổ dữ liệu: {times[-1] - times[0]:.1f} s" if times else "Chưa có thời gian phiên")

    def select_page(self, index):
        self.stack.setCurrentIndex(index)
        self.page_title.setText(PAGES[index][0])
        for number, button in enumerate(self.nav_buttons):
            button.setChecked(number == index)
            button.setIcon(navigation_icon(number, number == index))
