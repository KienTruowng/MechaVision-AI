"""Trang Giám sát: viewport, KPI và trạng thái từ phiên đang xử lý."""

import math
import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, QRectF
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QTableWidgetItem,
    QSizePolicy,
    QPushButton,
    QTabWidget,
    QPlainTextEdit,
    QGridLayout,
)
from .dashboard_theme import COLORS
from .dashboard_widgets import (
    panel,
    viewport_icon,
    text_label,
    badge,
    set_tone,
    KpiCard,
    ImageSurface,
    TwinSurface,
    table,
)
from .i18n import status_text
from .geometry import Geometry

SOURCE_LABELS = {
    "simulation": "MÔ PHỎNG",
    "camera": "CAMERA TRỰC TIẾP",
    "video": "VIDEO ĐÃ GHI",
}
SOURCE_NOTICES = {
    "simulation": "Dữ liệu tổng hợp • Không phải phép đo động cơ thực",
    "camera": "Phép đo từ camera • Độ chính xác phụ thuộc hiệu chuẩn và bố trí cơ cấu",
    "video": "Phân tích tệp đã ghi • Cần xác minh nguồn gốc video và hiệu chuẩn",
}
STATUS_TONES = {
    "TRACKING": "valid",
    "PREDICTED": "warning",
    "LOST": "error",
    "UNINITIALIZED": "muted",
}
STATUS_DETAILS = {
    "TRACKING": "Có quan sát được chấp nhận. Độ bất định là ước lượng của bộ lọc, chưa phải độ chính xác đo thực.",
    "PREDICTED": "Dự báo ngắn hạn theo mô hình; chưa có quan sát mới được chấp nhận.",
    "LOST": "Không đủ độ tin cậy. Đã ngừng hiển thị góc, tốc độ và chuyển động mô hình.",
    "UNINITIALIZED": "Chưa khởi tạo. Cần quan sát chốt khuỷu để bắt đầu ước lượng.",
}


def value_text(value, precision=1):
    return (
        "—" if value is None or not math.isfinite(value) else f"{value:.{precision}f}"
    )


class KpiStrip(QWidget):
    def __init__(self, columns=None, compact=False, show_state=True):
        super().__init__()
        layout = QGridLayout(self) if columns else QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(9)
        self.labels = {}
        self.cards = {}
        for name, title, unit, caption in [
            ("angle", "Góc quay", "°", "Góc liên tục · EKF vật lý"),
            ("rpm", "Tốc độ quay", "vòng/phút", "Có dấu theo chiều quay"),
            ("discrepancy", "Sai lệch động học", "px", "Quan sát / mô hình"),
            ("sigma", "Độ bất định", "°", "σθ của bộ lọc"),
            ("fps", "Nhịp xử lý", "khung/s", "Nhịp cập nhật phiên"),
            (
                "confidence",
                "Tin cậy điểm",
                "0–1",
                "Điểm thấp nhất trong các keypoint hiện có; không phải xác suất đúng",
            ),
            ("state", "Trạng thái", "", "Chất lượng theo dõi"),
        ]:
            if compact:
                title = {
                    "rpm": "RPM",
                    "fps": "FPS",
                    "discrepancy": "Sai lệch",
                    "sigma": "Bất định",
                    "confidence": "Tin cậy",
                }.get(name, title)
            card = KpiCard(title, unit, caption, state=name == "state", compact=compact)
            if name in ("angle", "rpm"):
                card.value.setStyleSheet(
                    "color:#70def2;"
                    + ("font-size:30px; font-weight:600;" if compact else "")
                )
            self.labels[name] = card.value
            self.cards[name] = card
            if name == "state" and not show_state:
                card.setParent(self)
                card.hide()
            elif columns:
                index = len(self.cards) - 1
                layout.addWidget(card, index // columns, index % columns)
            else:
                layout.addWidget(card, 1)
        self.labels["sigma"].setToolTip(
            "Độ lệch chuẩn góc do EKF ước lượng; cần kiểm chứng hiệu chuẩn riêng."
        )
        self.labels["fps"].setToolTip(
            "Nhịp gọi luồng xử lý hiện có; không phải độ trễ toàn trình camera hoặc benchmark GPU."
        )
        self.labels["discrepancy"].setToolTip(
            "Sai lệch vị trí pít-tông so với góc chốt khuỷu theo mô hình; không chẩn đoán hư hỏng."
        )

    def clear(self):
        for label in self.labels.values():
            label.setText("—")
        self.labels["state"].setStyleSheet("")
        for card in self.cards.values():
            card.sparkline.set_values([])

    def update_trends(self, state):
        points = list(state.observation.landmarks.values()) if state.observation else []
        scores = [p.confidence for p in points if math.isfinite(p.confidence)]
        self.labels["confidence"].setText(
            value_text(min(scores) if scores else None, 2)
        )
        self.cards["confidence"].setToolTip(
            f"Điểm nhỏ nhất trong {len(scores)}/3 keypoint hiện có; không phải xác suất đúng hoặc độ chính xác mô hình."
        )
        for name, series in [
            ("angle", "physics_angle"),
            ("rpm", "physics_rpm"),
            ("discrepancy", "discrepancy"),
            ("sigma", "physics_sigma"),
            ("fps", "fps"),
        ]:
            self.cards[name].sparkline.set_values(state.series[series])
            self.cards[name].sparkline.setToolTip(
                ("Mô phỏng" if state.mode == "simulation" else "Dữ liệu nguồn phiên")
                + " · Tối đa 90 mẫu gần nhất; không phải chỉ số đánh giá độ chính xác."
            )

    def update_metrics(self, metrics):
        est = metrics["physics"]
        self.labels["angle"].setText(
            value_text(math.degrees(est.theta) if est.theta is not None else None)
        )
        self.labels["rpm"].setText(value_text(est.rpm))
        self.labels["discrepancy"].setText(value_text(est.kinematic_discrepancy_px))
        self.labels["sigma"].setText(
            value_text(
                math.degrees(est.sigma_theta) if est.sigma_theta is not None else None
            )
        )
        self.labels["fps"].setText(
            value_text(metrics["fps"] if metrics["fps"] > 0 else None)
        )
        self.labels["state"].setText(status_text(est.status))
        color = {
            "TRACKING": COLORS["valid"],
            "PREDICTED": COLORS["warning"],
            "LOST": COLORS["error"],
        }.get(est.status, COLORS["muted"])
        self.labels["state"].setStyleSheet(f"color:{color};")


def make_plot(y_label, unit, legend=True):
    plot = pg.PlotWidget(background=COLORS["panel"])
    plot.setMinimumSize(160, 100)
    item = plot.getPlotItem()
    item.setLabel("left", y_label, units=unit, color=COLORS["muted"])
    item.setLabel("bottom", "Thời gian phiên", units="s", color=COLORS["muted"])
    item.showGrid(x=False, y=True, alpha=0.12)
    item.setDefaultPadding(0.04)
    item.setMenuEnabled(True)
    for axis in ("left", "bottom"):
        item.getAxis(axis).setPen(pg.mkPen("#30445b"))
        item.getAxis(axis).setTextPen(pg.mkPen("#8ca3bc"))
        item.getAxis(axis).setStyle(autoExpandTextSpace=True)
        item.getAxis(axis).enableAutoSIPrefix(False)
    if legend:
        key = item.addLegend(
            offset=(10, 6), labelTextColor="#aebfd2", labelTextSize="9pt"
        )
        key.setColumnCount(3)
        key.setBrush(pg.mkBrush(14, 28, 46, 215))
        key.setPen(pg.mkPen(None))
    return plot


def curve(plot, name, color, width=2, dashed=False):
    pen = pg.mkPen(color, width=width, style=Qt.DashLine if dashed else Qt.SolidLine)
    return plot.plot(pen=pen, name=name, connect="finite", antialias=True)


class MonitoringPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.kpis = KpiStrip(columns=3, compact=True, show_state=False)
        notice = QHBoxLayout()
        self.source_badge = badge("CHƯA CÓ NGUỒN", "muted")
        self.source_badge.setMinimumWidth(126)
        notice.addWidget(self.source_badge)
        self.banner = text_label(
            "Bắt đầu phiên mô phỏng hoặc cấu hình camera/video để quan sát.",
            "muted",
            True,
        )
        notice.addWidget(self.banner, 1)
        self.tracking_badge = badge("CHƯA CÓ DỮ LIỆU", "muted")
        self.tracking_badge.setMinimumWidth(132)
        notice.addWidget(self.tracking_badge)
        self.banner.hide()
        self.source_badge.hide()
        self.tracking_badge.hide()

        self.media_splitter = QSplitter(Qt.Horizontal)
        self.media_splitter.setHandleWidth(8)
        self.media_splitter.setChildrenCollapsible(False)
        self.camera_meta = text_label("Chờ nguồn", "muted")
        self.camera_meta.setMinimumWidth(164)
        self.camera_meta.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        camera, camera_layout = panel("01  Quan sát thị giác")
        self.camera = ImageSurface(
            "Chưa có khung hình", "Bắt đầu phiên để xem ảnh và điểm đặc trưng."
        )
        self._geometry = Geometry()
        self.focus_button = QPushButton("Cận cảnh")
        self.focus_button.setCheckable(True)
        self.focus_button.setChecked(True)
        self.focus_button.setToolTip(
            "Cận cảnh cố định theo hình học hiệu chuẩn; không đổi ảnh gốc hoặc tọa độ đo. "
            "Tắt để xem toàn bộ khung nguồn."
        )
        self.focus_button.setStyleSheet("padding:4px 9px; font-size:11px;")
        self.focus_button.toggled.connect(self._update_focus)
        controls = QHBoxLayout()
        self.annotation_button = QPushButton("Điểm, nhãn")
        self.annotation_button.setCheckable(True)
        self.annotation_button.setChecked(True)
        self.annotation_button.toggled.connect(self._annotations)
        self.fit_button = QPushButton()
        self.fit_button.setIcon(viewport_icon("fit"))
        self.fit_button.setToolTip("Vừa khung · đặt lại zoom và pan")
        self.fit_button.clicked.connect(self._fit_camera)
        controls.addWidget(self.annotation_button)
        controls.addWidget(self.focus_button)
        controls.addStretch()
        camera_layout.itemAt(0).layout().addLayout(controls)
        camera_layout.addWidget(self.camera, 1)
        key = QHBoxLayout()
        self.keypoint_labels = {}
        for name, title, color in [
            ("pivot", "Tâm quay", "#d3e2ee"),
            ("crank", "Chốt khuỷu", "#50d4ed"),
            ("piston", "Khớp pít-tông", "#48d5b1"),
        ]:
            label = text_label(title + " · —", "micro")
            self.keypoint_labels[name] = (label, title)
            label.setStyleSheet("color:" + color + ";")
            key.addWidget(label)
        key.addStretch()

        camera_layout.addLayout(key)
        key.addWidget(self.camera_meta)
        self.camera_meta.setMinimumWidth(0)
        self.zoom_minus = QPushButton("−")
        self.zoom_plus = QPushButton("+")
        self.zoom_text = text_label("1.00×", "micro")
        for button, change in [(self.zoom_minus, -0.25), (self.zoom_plus, 0.25)]:
            button.setObjectName("compact")
            button.setFixedWidth(26)
            button.clicked.connect(
                lambda checked=False, change=change: self._zoom(change)
            )
        controls.addWidget(self.zoom_minus)
        controls.addWidget(self.zoom_text)
        controls.addWidget(self.zoom_plus)
        controls.addWidget(self.fit_button)
        self.zoom_plus.setToolTip(
            "Phóng to phần hiển thị; giữ nguyên ảnh gốc và kết quả đo"
        )
        twin, twin_layout = panel(
            "02  Bản sao số",
        )
        self.twin = TwinSurface(
            "Chưa có trạng thái ước lượng",
            "Mô hình chỉ cập nhật khi có ước lượng hợp lệ hoặc dự báo.",
        )
        twin_controls = QHBoxLayout()
        self.twin_source = text_label("Ước lượng chưa khả dụng", "micro")
        self.twin_source.setToolTip("Bản vẽ từ EKF vật lý; không phải cảm biến độc lập")
        self.twin_zoom_minus = QPushButton("−")
        self.twin_zoom_plus = QPushButton("+")
        self.twin_fit_button = QPushButton()
        self.twin_fit_button.setIcon(viewport_icon("fit"))
        self.twin_fit_button.setToolTip("Bản sao số · vừa khung")
        for button, change in [
            (self.twin_zoom_minus, -0.25),
            (self.twin_zoom_plus, 0.25),
        ]:
            button.setObjectName("compact")
            button.setFixedWidth(26)
            button.clicked.connect(
                lambda checked=False, change=change: self.twin.set_zoom(
                    self.twin.zoom_factor + change
                )
            )
            twin_controls.addWidget(button)
        self.twin_fit_button.clicked.connect(self.twin.fit_view)
        twin_controls.addWidget(self.twin_fit_button)
        twin_layout.itemAt(0).layout().addLayout(twin_controls)
        twin_layout.addWidget(self.twin, 1)
        twin_layout.addWidget(
            text_label(
                "O · Trục quay     C · Chốt khuỷu     S · Khớp pít-tông", "muted"
            )
        )
        self.media_splitter.addWidget(camera)
        self.media_splitter.addWidget(twin)
        self.media_splitter.setSizes([560, 440])
        self.media_splitter.setStretchFactor(0, 56)
        self.media_splitter.setStretchFactor(1, 44)
        for button in (
            self.annotation_button,
            self.focus_button,
            self.fit_button,
            self.twin_fit_button,
        ):
            button.setFixedSize(32, 32)
        self.annotation_button.setText("")
        self.annotation_button.setIcon(viewport_icon("annotations"))
        self.annotation_button.setToolTip("Bật/tắt điểm và chú thích · kéo ảnh để pan")
        self.focus_button.setIcon(viewport_icon("focus"))
        layout.addWidget(self.media_splitter, 1)

        bottom_widget = QWidget()
        bottom_widget.setFixedHeight(196)
        self.bottom_widget = bottom_widget
        bottom_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        bottom = QHBoxLayout(bottom_widget)
        bottom.setContentsMargins(0, 0, 0, 0)
        bottom.setSpacing(10)
        trend, trend_layout = panel("Xu hướng góc · 15 s")
        self.overview = make_plot("Góc", "°")
        self.raw_curve = curve(self.overview, "Thị giác", "#F1BE62", 1.5)
        self.temporal_curve = curve(
            self.overview, "EKF thời gian", "#A696FF", 1.75, True
        )
        self.physics_curve = curve(self.overview, "EKF vật lý", "#50d4ed", 2)
        self.overview.getPlotItem().legend.hide()
        legend_row = QHBoxLayout()
        legend_row.setSpacing(8)
        for title, color in [
            ("— Thị giác", "#F1BE62"),
            ("– EKF thời gian", "#A696FF"),
            ("— EKF vật lý", "#52D7F1"),
        ]:
            label = text_label(title, "micro")
            label.setStyleSheet(f"color:{color}; font-size:12px;")
            legend_row.addWidget(label)
        legend_row.addStretch()
        trend_layout.addLayout(legend_row)
        self.overview.showGrid(x=False, y=True, alpha=0.08)
        trend_layout.addWidget(self.overview, 1)
        status, status_layout = panel("Trạng thái phiên")
        self.status_table = table(["Thành phần", "Quan sát hiện tại"])
        self.status_table.horizontalHeader().hide()
        self.status_table.setRowCount(3)
        self.status_table.verticalHeader().setDefaultSectionSize(25)
        self.status_table.verticalHeader().setMinimumSectionSize(20)
        self.status_table.verticalHeader().setDefaultSectionSize(28)
        self.status_table.setStyleSheet(
            "QTableWidget::item { padding:3px 6px; font-size:13px; }"
        )
        for row, title in enumerate(
            ["Điểm quan sát", "Phép đo bộ lọc", "Khung đã nhận"]
        ):
            self.status_table.setItem(row, 0, QTableWidgetItem(title))
            self.status_table.setItem(row, 1, QTableWidgetItem("—"))
            self.status_table.item(row, 1).setTextAlignment(
                Qt.AlignRight | Qt.AlignVCenter
            )
        self.event_log = QPlainTextEdit()
        self.event_log.setReadOnly(True)
        self.event_log.setMaximumBlockCount(80)
        self.event_log.setPlaceholderText("Chưa có sự kiện phiên")
        self.event_tabs = QTabWidget()
        self.event_tabs.addTab(self.status_table, "Phiên")
        self.event_tabs.addTab(self.event_log, "Sự kiện")
        self._last_tracking = None
        status_layout.addWidget(self.event_tabs)
        metrics, metrics_layout = panel("Thông số ước lượng")
        metrics_layout.addWidget(self.kpis, 1)
        bottom.addWidget(metrics, 38)
        bottom.addWidget(trend, 37)
        bottom.addWidget(status, 25)
        layout.addWidget(bottom_widget)
        self.confidence_label = text_label(
            "Chưa có ước lượng để đánh giá độ tin cậy.", "muted", True
        )
        self.confidence_label.hide()
        self._update_focus()

    def resizeEvent(self, event):
        self.bottom_widget.setFixedHeight(196)
        super().resizeEvent(event)

    def add_event(self, message):
        self.event_log.appendPlainText(message)

    def _annotations(self, checked):
        self.camera.show_annotations = checked
        self.camera.update()

    def _fit_camera(self):
        self.camera.fit_view()
        self.zoom_text.setText("1.00×")

    def _zoom(self, change):
        self.camera.set_zoom(self.camera.zoom_factor + change)
        self.zoom_text.setText(f"{self.camera.zoom_factor:.2f}×")

    def set_geometry(self, geometry):
        self._geometry = geometry
        self._update_focus()

    def _update_focus(self):
        # Miền cố định toàn vòng, có lề cho nhãn; không bám theo nhiễu từng khung.
        points = np.concatenate(
            [
                list(self._geometry.points(theta).values())
                for theta in np.linspace(0, 2 * math.pi, 181)
            ]
        )
        low, high = points.min(axis=0), points.max(axis=0)
        rect = QRectF(
            float(low[0] - 24),
            float(low[1] - 30),
            float(high[0] - low[0] + 48),
            float(high[1] - low[1] + 60),
        )
        focused = self.focus_button.isChecked()
        self.camera.set_focus_rect(rect if focused else None)
        self.focus_button.setText("")
        self.focus_button.setToolTip(
            "Cận cảnh theo hiệu chuẩn" if focused else "Toàn khung nguồn"
        )
        self.focus_button.setAccessibleName("Cận cảnh" if focused else "Toàn khung")

    def prepare(self, mode):
        self.camera.clear()
        self.camera.source_caption = (
            "SIMULATION · MÔ PHỎNG" if mode == "simulation" else SOURCE_LABELS[mode]
        )
        self.event_log.clear()
        self._last_tracking = None
        self.add_event("Bắt đầu · " + SOURCE_LABELS[mode])
        self.twin_source.setText("Ước lượng từ " + SOURCE_LABELS[mode].lower())
        self.twin.clear()
        self.kpis.clear()
        self.camera.set_zoom(1)
        self.zoom_text.setText("1.00×")
        for label, title in self.keypoint_labels.values():
            label.setText(title + " · —")
        self.source_badge.setText(SOURCE_LABELS[mode])
        set_tone(self.source_badge, "warning" if mode == "simulation" else "data")
        self.banner.setText(SOURCE_NOTICES[mode])
        self.tracking_badge.setText(
            "ĐANG KẾT NỐI" if mode == "camera" else "ĐANG KHỞI ĐỘNG"
        )
        set_tone(self.tracking_badge, "warning")
        self.camera_meta.setText("Đang chờ khung đầu tiên")
        self.confidence_label.setText(
            "Chưa nhận được dữ liệu. Chưa hiển thị giá trị ước lượng."
        )
        for row in range(3):
            self.status_table.item(row, 1).setText("—")
        for item in (self.raw_curve, self.temporal_curve, self.physics_curve):
            item.clear()

    def update_state(self, state, frame, twin, raw_frame=None):
        obs, metrics = state.observation, state.metrics
        est = metrics["physics"]
        self.camera.set_frame(frame if raw_frame is None else raw_frame)
        self.camera.set_overlay(obs if raw_frame is not None else None)
        if est.status != self._last_tracking:
            self.add_event(f"{obs.timestamp:.2f} s · {status_text(est.status)}")
            self._last_tracking = est.status
        self.twin.set_estimate(self._geometry, est)
        self.kpis.update_metrics(metrics)
        self.kpis.update_trends(state)
        for name, (label, title) in self.keypoint_labels.items():
            point = obs.landmarks.get(name)
            score = value_text(point.confidence, 2) if point is not None else "—"
            label.setText(title + " · " + score)
            label.setToolTip(
                "Điểm tin cậy quan sát trên thang 0–1, không phải xác suất đúng. "
                + (
                    "Quan sát tổng hợp mô phỏng."
                    if state.mode == "simulation"
                    else "Giá trị do detector cung cấp."
                )
            )
        self.tracking_badge.setText(status_text(est.status).upper())
        set_tone(self.tracking_badge, STATUS_TONES.get(est.status, "muted"))
        self.camera_meta.setText(f"Khung {obs.frame_id} · {obs.timestamp:.2f} s")
        self.confidence_label.setText(
            STATUS_DETAILS.get(est.status, "Trạng thái chưa được nhận diện.")
        )
        for row, text in enumerate(
            [
                f"{len(obs.landmarks)} / 3 điểm",
                f"{est.observation_count} nhận · {est.rejected_count} loại",
                str(state.sample_count),
            ]
        ):
            self.status_table.item(row, 1).setText(text)
        if state.sample_count % 3 == 0 or state.sample_count == 1:
            times = np.asarray(state.series["time"])
            times = times - times[0]
            for item, name in [
                (self.raw_curve, "raw_angle"),
                (self.temporal_curve, "temporal_angle"),
                (self.physics_curve, "physics_angle"),
            ]:
                item.setData(times, list(state.series[name]), connect="finite")
            self.overview.setXRange(
                max(0, times[-1] - 15), max(1, times[-1]), padding=0.02
            )
