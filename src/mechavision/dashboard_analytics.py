"""Không gian nghiên cứu: chỉ vẽ kết quả gốc và giữ khoảng trống dữ liệu."""

from collections import deque
from PySide6.QtGui import QFont
from .i18n import status_text
import math
import numpy as np
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QComboBox,
    QCheckBox,
    QPushButton,
    QTabWidget,
    QFrame,
)
from .dashboard_widgets import panel, text_label, badge, set_tone
from .dashboard_monitoring import KpiStrip, make_plot, curve, SOURCE_LABELS


class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        self._last_sample = 0
        self.diagnostics = {
            name: deque(maxlen=3600)
            for name in ("time", "pivot", "crank", "piston", "processing_ms")
        }
        outer = QHBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)
        rail = QFrame()
        rail.setObjectName("panel")
        rail.setFixedWidth(240)
        rail_layout = QVBoxLayout(rail)
        rail_layout.setContentsMargins(8, 16, 8, 16)
        rail_layout.setSpacing(12)
        rail_layout.addWidget(text_label("TỔNG QUAN PHIÊN", "eyebrow"))
        rail_layout.addWidget(text_label("Chỉ số\nước lượng", "section_title"))
        self.kpis = KpiStrip(columns=2, compact=True, show_state=False)
        rail_layout.addWidget(self.kpis)
        for name, card in self.kpis.cards.items():
            if name in ("angle", "rpm", "sigma", "fps", "discrepancy"):
                card.sparkline.setFixedHeight(22)
                card.sparkline.show()
        rail_layout.addSpacing(8)
        rail_layout.addWidget(text_label("PHẠM VI DỮ LIỆU", "eyebrow"))
        self.session_summary = text_label("Chưa có phiên dữ liệu", "muted", True)
        self.session_summary.setStyleSheet("font-size:13px; color:#CAD8E8;")
        rail_layout.addWidget(self.session_summary)
        rail_layout.addWidget(text_label("ĐỌC KẾT QUẢ", "eyebrow"))
        rail_layout.addWidget(
            text_label(
                "Góc và tốc độ từ EKF vật lý. Độ bất định là ước lượng của bộ lọc, chưa phải sai số đo thực.",
                "muted",
                True,
            )
        )
        rail_layout.addWidget(
            text_label(
                "Ba phương pháp dùng cùng luồng quan sát. Mẫu thiếu giữ khoảng trống trên đồ thị.",
                "muted",
                True,
            )
        )
        rail_layout.addStretch()
        outer.addWidget(rail)
        layout = QVBoxLayout()
        layout.setSpacing(10)
        outer.addLayout(layout, 1)
        heading = QHBoxLayout()
        heading.addWidget(
            text_label("Động học & chất lượng ước lượng", "section_title")
        )
        heading.addStretch()
        self.export_button = QPushButton("Xuất biểu đồ")
        heading.addWidget(self.export_button)
        layout.addLayout(heading)
        toolbar = QHBoxLayout()
        self.raw_check = QCheckBox("Thị giác trực tiếp")
        self.temporal_check = QCheckBox("EKF thời gian")
        self.physics_check = QCheckBox("EKF vật lý")
        for check in (self.raw_check, self.temporal_check, self.physics_check):
            check.setChecked(True)
            toolbar.addWidget(check)
        toolbar.addStretch()
        self.follow_check = QCheckBox("Theo thời gian")
        self.follow_check.setChecked(True)
        toolbar.addWidget(self.follow_check)
        self.time_window = QComboBox()
        for title, value in [
            ("15 giây", 15),
            ("30 giây", 30),
            ("60 giây", 60),
            ("Toàn bộ bộ đệm", 0),
        ]:
            self.time_window.addItem(title, value)
        self.time_window.setCurrentIndex(1)
        toolbar.addWidget(self.time_window)
        layout.addLayout(toolbar)
        self.tabs = QTabWidget()
        self.tabs.setObjectName("research_tabs")
        self.angle_plot = make_plot("Góc liên tục", "°")
        self.rpm_plot = make_plot("Tốc độ quay", "vòng/phút")
        self.piston_plot = make_plot("Tọa độ trượt", "px")
        self.sigma_plot = make_plot("Độ bất định σθ", "°")
        self.discrepancy_plot = make_plot("Sai lệch động học", "px", legend=False)
        self.confidence_plot = make_plot("Tin cậy điểm", "")
        self.confidence_plot.setYRange(0, 1, padding=0.04)
        self.fps_plot = make_plot("Nhịp xử lý", "khung/s", legend=False)
        self.processing_plot = make_plot("Xử lý ước lượng", "ms", legend=False)
        self._add_tab(
            "Động học",
            [
                (0, 0, 5, "Góc quay · ba phương pháp", self.angle_plot),
                (1, 0, 3, "Tọa độ pít-tông · trục cục bộ", self.piston_plot),
                (1, 3, 2, "Tốc độ quay", self.rpm_plot),
            ],
        )
        self._add_tab(
            "Chất lượng quan sát",
            [
                (0, 0, 1, "Sai lệch động học", self.discrepancy_plot),
                (0, 1, 1, "Độ bất định góc", self.sigma_plot),
                (1, 0, 2, "Tin cậy từng điểm quan sát", self.confidence_plot),
            ],
            "Confidence do detector hoặc bộ mô phỏng cung cấp, không phải xác suất đúng. Sai lệch động học không phải innovation EKF hay chẩn đoán hư hỏng.",
        )
        self._add_tab(
            "Hiệu năng xử lý",
            [
                (0, 0, 1, "NHỊP CẬP NHẬT PHIÊN", self.fps_plot),
                (1, 0, 1, "THỜI GIAN XỬ LÝ BỘ ƯỚC LƯỢNG", self.processing_plot),
            ],
            "Processor.step gồm ba bộ ước lượng và ghi CSV; không gồm camera, detector, hiển thị. Độ trễ toàn trình: chưa khả dụng. Chưa xác minh hiệu năng GPU.",
        )
        layout.addWidget(self.tabs, 1)
        self.source_badge = badge("CHƯA CÓ DỮ LIỆU", "muted")
        self.data_note = text_label(
            "Bắt đầu phiên để xem chuỗi dữ liệu; không có đường minh họa được tạo sẵn.",
            "muted",
            True,
        )
        bottom = QHBoxLayout()
        bottom.addWidget(self.source_badge)
        bottom.addWidget(self.data_note, 1)
        layout.addLayout(bottom)
        self.curves = {
            "raw_angle": curve(
                self.angle_plot, "Góc từ điểm đặc trưng", "#f0bf65", 1.4
            ),
            "temporal_angle": curve(
                self.angle_plot, "EKF thời gian", "#9e8aff", 1.8, True
            ),
            "physics_angle": curve(self.angle_plot, "EKF vật lý", "#50d4ed", 2.2),
            "temporal_rpm": curve(self.rpm_plot, "EKF thời gian", "#9e8aff", 1.8, True),
            "physics_rpm": curve(self.rpm_plot, "EKF vật lý", "#50d4ed", 2.2),
            "temporal_sigma": curve(
                self.sigma_plot, "EKF thời gian", "#9e8aff", 1.8, True
            ),
            "physics_sigma": curve(self.sigma_plot, "EKF vật lý", "#50d4ed", 2.2),
            "piston_observed": curve(self.piston_plot, "Quan sát", "#f0bf65", 1.5),
            "piston_estimated": curve(self.piston_plot, "EKF vật lý", "#50d4ed", 2.2),
            "discrepancy": curve(
                self.discrepancy_plot, "Sai lệch vị trí pít-tông", "#f0bf65", 1.8
            ),
            "fps": curve(self.fps_plot, "Nhịp xử lý phiên", "#48d5b1", 1.8),
        }
        self.confidence_curves = {
            name: curve(self.confidence_plot, title, color, 1.8)
            for name, title, color in [
                ("pivot", "Tâm quay", "#b8c8df"),
                ("crank", "Chốt khuỷu", "#50d4ed"),
                ("piston", "Khớp pít-tông", "#9e8aff"),
            ]
        }
        self.processing_curve = curve(
            self.processing_plot, "Ba bộ ước lượng + CSV", "#9e8aff", 1.8
        )
        for check in (self.raw_check, self.temporal_check, self.physics_check):
            check.toggled.connect(self._update_visibility)
        self.export_button.clicked.connect(self._export_current)
        for name, line in self.curves.items():
            pen = line.opts["pen"]
            pen.setWidthF(2.8 if name.startswith("physics") else 2.1)
            line.setPen(pen)
        font = QFont(self.font().family())
        font.setPixelSize(13)
        for plot in self.plots:
            item = plot.getPlotItem()
            for axis_name in ("left", "bottom"):
                axis = item.getAxis(axis_name)
                axis.setStyle(tickFont=font)
                axis.label.setFont(font)
                axis.setTextPen("#B5C6DA")
            item.showGrid(x=False, y=True, alpha=0.08)
            if item.legend:
                item.legend.setLabelTextSize("13px")
        self.data_note.setText(
            "Chưa có dữ liệu · Bắt đầu phiên tại thanh điều khiển để xem quan sát và ước lượng."
        )

    def _add_tab(self, title, specs, note=None):
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(0, 10, 0, 0)
        grid = QGridLayout()
        grid.setSpacing(10)
        for row, column, span, label, plot in specs:
            card, inside = panel(label)
            inside.addWidget(plot, 1)
            grid.addWidget(card, row, column, 1, span)
            grid.setRowStretch(row, 1)
            for index in range(column, column + span):
                grid.setColumnStretch(index, 1)
        layout.addLayout(grid, 1)
        if note:
            layout.addWidget(text_label(note, "muted", True))
        self.tabs.addTab(page, title)

    @property
    def plots(self):
        return [
            self.angle_plot,
            self.rpm_plot,
            self.piston_plot,
            self.sigma_plot,
            self.discrepancy_plot,
            self.confidence_plot,
            self.fps_plot,
            self.processing_plot,
        ]

    def _export_current(self):
        plot = [self.angle_plot, self.discrepancy_plot, self.fps_plot][
            self.tabs.currentIndex()
        ]
        plot.scene().exportDialog.show(plot.getPlotItem())

    def _update_visibility(self):
        for name, item in self.curves.items():
            if name == "fps":
                continue
            visible = (
                self.raw_check.isChecked()
                if name.startswith("raw") or name == "piston_observed"
                else self.temporal_check.isChecked()
                if name.startswith("temporal")
                else self.physics_check.isChecked()
            )
            item.setVisible(visible)

    def clear(self):
        self.session_summary.setText("Chưa có phiên dữ liệu")
        self.kpis.clear()
        self._last_sample = 0
        for values in self.diagnostics.values():
            values.clear()
        for item in [
            *self.curves.values(),
            *self.confidence_curves.values(),
            self.processing_curve,
        ]:
            item.clear()
        self.source_badge.setText("CHƯA CÓ DỮ LIỆU")
        set_tone(self.source_badge, "muted")
        self.data_note.setText(
            "Bắt đầu phiên để xem chuỗi dữ liệu; không có đường minh họa được tạo sẵn."
        )

    def record_observation(self, state):
        if (
            state.metrics is None
            or state.observation is None
            or state.sample_count == self._last_sample
        ):
            return
        if state.sample_count < self._last_sample:
            self.clear()
        self._last_sample = state.sample_count
        self.diagnostics["time"].append(state.observation.timestamp)
        for name in ("pivot", "crank", "piston"):
            point = state.observation.landmarks.get(name)
            self.diagnostics[name].append(
                float(point.confidence) if point is not None else float("nan")
            )
        timing = state.metrics.get("processing_ms")
        self.diagnostics["processing_ms"].append(
            float(timing)
            if timing is not None and math.isfinite(timing)
            else float("nan")
        )

    def update_state(self, state):
        if state.metrics is None:
            return
        self.record_observation(state)
        self.kpis.update_metrics(state.metrics)
        self.kpis.update_trends(state)
        times = np.asarray(state.series["time"])
        times = times - times[0]
        estimate = state.metrics["physics"]
        self.session_summary.setText(
            f"{state.sample_count:,} khung đã nhận\n"
            f"{times[-1]:.2f} s trong bộ đệm\n"
            f"{len(state.observation.landmarks)}/3 điểm ở khung cuối\n"
            f"{status_text(estimate.status)} · khung cuối"
        )
        for name, item in self.curves.items():
            item.setData(times, list(state.series[name]), connect="finite")
        diagnostic_time = np.asarray(self.diagnostics["time"]) - state.series["time"][0]
        for name, item in self.confidence_curves.items():
            item.setData(
                diagnostic_time, list(self.diagnostics[name]), connect="finite"
            )
        self.processing_curve.setData(
            diagnostic_time, list(self.diagnostics["processing_ms"]), connect="finite"
        )
        self.source_badge.setText(SOURCE_LABELS[state.mode])
        set_tone(self.source_badge, "warning" if state.mode == "simulation" else "data")
        self.data_note.setText(
            f"{state.sample_count:,} khung đã nhận · "
            + (
                "Dữ liệu tổng hợp, không phải thực nghiệm vật lý."
                if state.mode == "simulation"
                else "Dữ liệu của nguồn phiên; chưa xác minh tham chiếu vật lý độc lập."
            )
        )
        if self.follow_check.isChecked():
            window = self.time_window.currentData()
            start = max(0, times[-1] - window) if window else 0
            for plot in self.plots:
                plot.setXRange(start, max(1, times[-1]), padding=0.02)
