"""Trang Phân tích: chỉ vẽ các chuỗi kết quả gốc được lưu trong DashboardState."""

import numpy as np
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QComboBox,
    QCheckBox,
    QPushButton,
)
from .dashboard_widgets import panel, text_label
from .dashboard_monitoring import KpiStrip, make_plot, curve


class AnalyticsPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        self.kpis = KpiStrip()
        layout.addWidget(self.kpis)
        toolbar = QHBoxLayout()
        self.raw_check = QCheckBox("Thị giác trực tiếp")
        self.temporal_check = QCheckBox("EKF thời gian")
        self.physics_check = QCheckBox("EKF vật lý")
        for checkbox in (self.raw_check, self.temporal_check, self.physics_check):
            checkbox.setChecked(True)
            toolbar.addWidget(checkbox)
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
        self.export_button = QPushButton("Xuất biểu đồ")
        toolbar.addWidget(self.export_button)
        layout.addLayout(toolbar)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.angle_plot = make_plot("Góc liên tục", "°")
        self.rpm_plot = make_plot("Tốc độ quay", "vòng/phút")
        self.sigma_plot = make_plot("Độ bất định σθ", "°")
        self.discrepancy_plot = make_plot("Sai lệch động học", "px", legend=False)
        for row, column, title, plot in [
            (0, 0, "GÓC QUAY / SO SÁNH BA PHƯƠNG PHÁP", self.angle_plot),
            (0, 1, "VẬN TỐC / BỘ LỌC THEO THỜI GIAN", self.rpm_plot),
            (1, 0, "ĐỘ BẤT ĐỊNH / ƯỚC LƯỢNG CỦA BỘ LỌC", self.sigma_plot),
            (1, 1, "ĐỘ NHẤT QUÁN / QUAN SÁT VÀ MÔ HÌNH", self.discrepancy_plot),
        ]:
            card, inner = panel(title)
            inner.addWidget(plot, 1)
            grid.addWidget(card, row, column)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setRowStretch(0, 1)
        grid.setRowStretch(1, 1)
        layout.addLayout(grid, 1)
        self.curves = {
            "raw_angle": curve(
                self.angle_plot, "Góc từ điểm đặc trưng", "#f0bf65", 1.3
            ),
            "temporal_angle": curve(
                self.angle_plot, "EKF thời gian", "#438fff", 1.8, True
            ),
            "physics_angle": curve(self.angle_plot, "EKF vật lý", "#50d4ed", 2.2),
            "temporal_rpm": curve(self.rpm_plot, "EKF thời gian", "#438fff", 1.8, True),
            "physics_rpm": curve(self.rpm_plot, "EKF vật lý", "#50d4ed", 2.2),
            "temporal_sigma": curve(
                self.sigma_plot, "EKF thời gian", "#438fff", 1.8, True
            ),
            "physics_sigma": curve(self.sigma_plot, "EKF vật lý", "#50d4ed", 2.2),
            "discrepancy": curve(
                self.discrepancy_plot, "Sai lệch vị trí pít-tông", "#f0bf65", 1.8
            ),
        }
        for check in (self.raw_check, self.temporal_check, self.physics_check):
            check.toggled.connect(self._update_visibility)
        self.export_button.clicked.connect(
            lambda: self.angle_plot.scene().exportDialog.show(
                self.angle_plot.getPlotItem()
            )
        )
        layout.addWidget(
            text_label(
                "Cùng luồng quan sát • Ô thiếu dữ liệu tạo khoảng trống trên đồ thị • Bộ đệm tối đa 3.600 mẫu",
                "muted",
            )
        )

    @property
    def plots(self):
        return [self.angle_plot, self.rpm_plot, self.sigma_plot, self.discrepancy_plot]

    def _update_visibility(self):
        for name, item in self.curves.items():
            visible = (
                self.raw_check.isChecked()
                if name.startswith("raw")
                else (
                    self.temporal_check.isChecked()
                    if name.startswith("temporal")
                    else self.physics_check.isChecked()
                )
            )
            item.setVisible(visible)

    def clear(self):
        self.kpis.clear()
        for item in self.curves.values():
            item.clear()

    def update_state(self, state):
        if state.metrics is None:
            return
        self.kpis.update_metrics(state.metrics)
        times = np.asarray(state.series["time"])
        times = times - times[0]
        for name, item in self.curves.items():
            item.setData(times, list(state.series[name]), connect="finite")
        if self.follow_check.isChecked():
            window = self.time_window.currentData()
            start = max(0, times[-1] - window) if window else 0
            for plot in self.plots:
                plot.setXRange(start, max(1, times[-1]), padding=0.02)
