"""Giao diện thực nghiệm và lịch sử phiên của lần mở ứng dụng hiện tại."""

from datetime import datetime
from pathlib import Path
import math
import shutil
import pyqtgraph as pg
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QDoubleSpinBox,
    QSpinBox,
    QStackedWidget,
    QSplitter,
    QTableWidgetItem,
    QTabWidget,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QApplication,
)
from .dashboard_widgets import panel, text_label, badge, set_tone, table
from .dashboard_controller import EvaluationWorker
from .dashboard_monitoring import value_text, make_plot

METHOD_LABELS = {
    "raw_cv_baseline": "Thị giác trực tiếp",
    "raw_visual": "Thị giác trực tiếp",
    "temporal_ekf": "EKF thời gian",
    "physics_ekf": "EKF vật lý",
}


class ExperimentsPage(QWidget):
    def __init__(self, browse, notify, geometry_path):
        super().__init__()
        self.browse = browse
        self.notify = notify
        self.geometry_path = geometry_path
        self.worker = None
        self.last_output = None
        self.last_result = None
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        setup, setup_layout = panel(
            "Thiết kế thực nghiệm",
            trailing=badge("CÙNG QUAN SÁT · BA PHƯƠNG PHÁP", "data"),
        )
        controls = QHBoxLayout()
        controls.setSpacing(20)
        source = QVBoxLayout()
        self.mode = QComboBox()
        self.mode.addItem("Dữ liệu mô phỏng", "synthetic")
        self.mode.addItem("Quan sát đã ghi + tham chiếu", "recorded")
        source.addWidget(text_label("Nguồn đánh giá", "muted"))
        source.addWidget(self.mode)
        self.notice = text_label("", "muted", True)
        source.addWidget(self.notice)
        controls.addLayout(source, 3)
        self.inputs = QStackedWidget()
        synthetic = QWidget()
        grid = QGridLayout(synthetic)
        grid.setContentsMargins(0, 0, 0, 0)
        self.seconds = QDoubleSpinBox()
        self.seconds.setRange(1, 300)
        self.seconds.setValue(24)
        self.seconds.setSuffix(" s")
        self.fps = QSpinBox()
        self.fps.setRange(1, 120)
        self.fps.setValue(30)
        self.noise = QDoubleSpinBox()
        self.noise.setRange(0, 50)
        self.noise.setValue(3)
        self.noise.setSuffix(" px")
        self.seed = QSpinBox()
        self.seed.setRange(0, 2147483647)
        self.seed.setValue(42)
        for column, (title, widget) in enumerate(
            [
                ("Thời lượng", self.seconds),
                ("Khung/giây", self.fps),
                ("Nhiễu", self.noise),
                ("Hạt giống", self.seed),
            ]
        ):
            grid.addWidget(text_label(title, "muted"), 0, column)
            grid.addWidget(widget, 1, column)
        note = text_label(
            "Mỗi lần chạy lưu một báo cáo riêng. Tham số đánh giá giữ nguyên pipeline.",
            "muted",
            True,
        )
        grid.addWidget(note, 2, 0, 1, 4)
        self.inputs.addWidget(synthetic)
        recorded = QWidget()
        recorded_layout = QGridLayout(recorded)
        recorded_layout.setContentsMargins(0, 0, 0, 0)
        self.session_file = QLineEdit()
        self.truth_file = QLineEdit()
        self.geometry_file = QLineEdit()
        for row, (title, widget, kind) in enumerate(
            [
                ("CSV quan sát", self.session_file, "CSV (*.csv)"),
                ("CSV tham chiếu", self.truth_file, "CSV (*.csv)"),
                ("Hình học", self.geometry_file, "JSON (*.json)"),
            ]
        ):
            recorded_layout.addWidget(text_label(title, "muted"), row, 0)
            recorded_layout.addWidget(widget, row, 1)
            button = QPushButton("Chọn")
            button.clicked.connect(
                lambda checked=False, target=widget, file_filter=kind: self.browse(
                    target, file_filter
                )
            )
            recorded_layout.addWidget(button, row, 2)
        self.inputs.addWidget(recorded)
        controls.addWidget(self.inputs, 5)
        output = QVBoxLayout()
        output.addWidget(text_label("Thư mục kết quả", "muted"))
        self.output_root = QLineEdit("outputs/experiments")
        output.addWidget(self.output_root)
        self.run_button = QPushButton("Chạy đánh giá")
        self.run_button.setObjectName("primary")
        self.run_button.clicked.connect(self.run_evaluation)
        output.addWidget(self.run_button)
        controls.addLayout(output, 3)
        setup_layout.addLayout(controls)
        layout.addWidget(setup)

        right = QSplitter(Qt.Horizontal)
        right.setChildrenCollapsible(False)
        right.setHandleWidth(10)
        self.result_badge = badge("CHƯA CÓ BÁO CÁO", "muted")
        self.result_badge.setMinimumWidth(130)
        result, result_layout = panel("SO SÁNH THUẬT TOÁN", trailing=self.result_badge)
        self.result_note = text_label(
            "Chạy một thực nghiệm để xem kết quả. Chưa có số liệu được tạo hoặc nạp.",
            "muted",
            True,
        )
        result_layout.addWidget(self.result_note)
        self.results_table = table(
            ["Phương pháp", "MAE (°)", "RMSE (°)", "P95 (°)", "Bao phủ (%)"]
        )
        self.result_tabs = QTabWidget()
        self.result_chart = make_plot("Sai số góc", "°")
        self.result_chart.setMinimumHeight(120)
        self.result_tabs.addTab(self.result_chart, "Đối chiếu sai số")
        self.result_tabs.addTab(self.results_table, "Bảng kết quả")
        result_layout.addWidget(self.result_tabs, 1)
        self.result_bars = []
        self.output_label = text_label("Chưa có tệp kết quả", "muted", True)
        self.output_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        result_layout.addWidget(self.output_label)
        self.open_button = QPushButton("Mở thư mục kết quả")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_output)
        actions = QHBoxLayout()
        self.export_csv_button = QPushButton("Xuất CSV kết quả")
        self.export_csv_button.setEnabled(False)
        self.export_csv_button.clicked.connect(self.export_csv)
        self.copy_output_button = QPushButton("Sao chép đường dẫn")
        self.copy_output_button.setEnabled(False)
        self.copy_output_button.clicked.connect(
            lambda: (
                QApplication.clipboard().setText(str(Path(self.last_output).resolve()))
                if self.last_output
                else None
            )
        )
        actions.addWidget(self.copy_output_button)
        actions.addStretch()
        actions.addWidget(self.export_csv_button)
        actions.addWidget(self.open_button)
        result_layout.addLayout(actions)
        right.addWidget(result)
        history, history_layout = panel(
            "NHẬT KÝ PHIÊN", "Các phiên thực sự đã khởi chạy trong lần mở ứng dụng này."
        )
        self.sessions_table = table(
            ["Bắt đầu", "Nguồn", "Nhận diện", "Số khung", "Trạng thái"]
        )
        self.sessions_table.hide()
        self.session_list = QListWidget()
        self.session_list.setStyleSheet(
            "QListWidget { background:transparent; border:none; } QListWidget::item { padding:14px 8px; border-bottom:1px solid #29394E; }"
        )
        self.session_empty = text_label(
            "Chưa có phiên thu nhận. Bắt đầu phiên ở thanh điều khiển để ghi nhật ký.",
            "muted",
            True,
        )
        history_layout.addWidget(self.session_empty)
        self.history_summary = text_label("0 phiên · 0 khung", "session_value")
        history_layout.addWidget(self.history_summary)
        self.session_list.setMaximumHeight(220)
        history_layout.addWidget(self.session_list)
        history_layout.addWidget(text_label("CHI TIẾT PHIÊN ĐƯỢC CHỌN", "eyebrow"))
        self.session_details = text_label(
            "Chọn một phiên để xem nguồn và nhật ký.", "muted", True
        )
        self.session_details.setStyleSheet("font-size:13px; color:#C4D3E4;")
        history_layout.addWidget(self.session_details)
        self.copy_session_button = QPushButton("Sao chép đường dẫn CSV")
        self.copy_session_button.setEnabled(False)
        self.copy_session_button.clicked.connect(self._copy_session_path)
        history_layout.addWidget(self.copy_session_button)
        self.session_list.currentRowChanged.connect(self._show_session_details)
        history_layout.addStretch()
        history_layout.addWidget(text_label("THAM CHIẾU ĐỘC LẬP", "eyebrow"))
        history_layout.addWidget(
            text_label(
                "Dữ liệu mô phỏng không xác minh cơ cấu LEGO. Kết quả đã ghi cần góc tham chiếu độc lập và hình học phù hợp.",
                "muted",
                True,
            )
        )
        right.addWidget(history)
        right.setSizes([700, 300])
        right.setStretchFactor(0, 7)
        right.setStretchFactor(1, 3)
        layout.addWidget(right, 1)
        self.mode.currentIndexChanged.connect(self._mode_changed)
        self._mode_changed(0)

    @property
    def busy(self):
        return self.worker is not None and self.worker.isRunning()

    def _mode_changed(self, index):
        self.inputs.setCurrentIndex(index)
        self.inputs.setFixedHeight(
            max(106, self.inputs.currentWidget().minimumSizeHint().height())
        )
        self.notice.setText(
            "Mô phỏng kiểm chứng luồng phần mềm, không chứng minh độ chính xác trên động cơ thực."
            if index == 0
            else "Dùng cùng CSV quan sát cho ba bộ ước lượng. Người thực nghiệm phải xác minh nguồn video và tính độc lập của tham chiếu."
        )
        if index == 1 and not self.geometry_file.text():
            self.geometry_file.setText(self.geometry_path())

    def run_evaluation(self):
        if self.busy:
            return
        mode = self.mode.currentData()
        if mode == "synthetic":
            parameters = dict(
                seconds=self.seconds.value(),
                fps=self.fps.value(),
                seed=self.seed.value(),
                noise_px=self.noise.value(),
            )
        else:
            parameters = dict(
                session_file=self.session_file.text().strip(),
                truth_file=self.truth_file.text().strip(),
                geometry_file=self.geometry_file.text().strip(),
            )
            if not all(Path(value).is_file() for value in parameters.values()):
                self.notify(
                    "Thiếu dữ liệu thực nghiệm",
                    "Hãy chọn CSV quan sát, CSV góc tham chiếu và JSON hình học hiện có.",
                )
                return
        if not self.output_root.text().strip():
            self.notify(
                "Thiếu thư mục kết quả", "Hãy nhập thư mục để lưu kết quả đánh giá."
            )
            return
        output = Path(self.output_root.text().strip()) / datetime.now().strftime(
            "run_%Y%m%d_%H%M%S_%f"
        )
        self.worker = EvaluationWorker(mode, parameters, str(output))
        self.worker.completed.connect(
            lambda report, path, source=mode: self._show_result(report, path, source)
        )
        self.worker.failed.connect(self._error)
        self.worker.finished.connect(self._finished)
        self._enable_setup(False)
        self.results_table.setRowCount(0)
        self.result_chart.clear()
        self.result_chart.getPlotItem().legend.clear()
        self.result_bars.clear()
        self.export_csv_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.copy_output_button.setEnabled(False)
        self.last_output = None
        self.last_result = None
        self.output_label.setText("Chưa có báo cáo cho lần chạy này.")
        self.result_badge.setText("ĐANG ĐÁNH GIÁ")
        set_tone(self.result_badge, "warning")
        self.result_note.setText(
            "Đang chạy quy trình đánh giá. Giao diện giám sát vẫn có thể sử dụng."
        )
        self.worker.start()

    def _enable_setup(self, enabled):
        for widget in (self.mode, self.inputs, self.output_root, self.run_button):
            widget.setEnabled(enabled)

    def _show_result(self, report, path, source):
        self.last_result, self.last_output = report, path
        self.results_table.setRowCount(0)
        for name, values in report["methods"].items():
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            cells = [
                METHOD_LABELS.get(name, name),
                value_text(values.get("mae_deg"), 3),
                value_text(values.get("rmse_deg"), 3),
                value_text(values.get("p95_abs_error_deg"), 3),
                value_text(
                    values.get("coverage_pct", values.get("availability_pct")), 2
                ),
            ]
            for column, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                if column:
                    item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.results_table.setItem(row, column, item)
        self.result_badge.setText(
            "MÔ PHỎNG" if source == "synthetic" else "QUAN SÁT ĐÃ GHI"
        )
        set_tone(self.result_badge, "warning" if source == "synthetic" else "data")
        self.result_note.setText(
            "Kết quả mô phỏng • Không phải kết quả đo động cơ thực."
            if source == "synthetic"
            else "Kết quả đối chiếu CSV • Chỉ áp dụng cho khung có tham chiếu; chưa xác minh độc lập phần cứng."
        )
        self.output_label.setText("Đã lưu JSON và CSV · …/" + Path(path).name)
        self.output_label.setToolTip(str(Path(path).resolve()))
        self.copy_output_button.setEnabled(True)
        self.open_button.setEnabled(True)
        self.export_csv_button.setEnabled(True)
        methods = list(report["methods"].items())
        ticks = [
            (index, METHOD_LABELS.get(name, name))
            for index, (name, _) in enumerate(methods)
        ]
        self.result_chart.getPlotItem().getAxis("bottom").setTicks([ticks])
        self.result_chart.setLabel("bottom", "Phương pháp")
        for index, (key, title, color) in enumerate(
            [
                ("mae_deg", "MAE", "#50d4ed"),
                ("rmse_deg", "RMSE", "#a28bfa"),
                ("p95_abs_error_deg", "P95", "#f0bf65"),
            ]
        ):
            positions, values = [], []
            for method, (_, metrics) in enumerate(methods):
                value = metrics.get(key)
                if value is not None and math.isfinite(value):
                    positions.append(method + (index - 1) * 0.22)
                    values.append(value)
            bars = pg.BarGraphItem(
                x=positions,
                height=values,
                width=0.19,
                brush=color,
                pen=None,
                name=title,
            )
            self.result_chart.addItem(bars)
            self.result_bars.append((key, positions, values))

    def export_results_to(self, destination):
        """Sao chép CSV do pipeline đã ghi, không tính lại hay đổi schema."""
        if not self.last_output:
            raise ValueError("Chưa có kết quả để xuất")
        candidates = [
            Path(self.last_output) / name
            for name in ("ablation.csv", "real_ablation.csv")
            if (Path(self.last_output) / name).is_file()
        ]
        if not candidates:
            raise ValueError("Pipeline chưa tạo tệp CSV")
        source = candidates[0]
        if source.resolve() != Path(destination).resolve():
            shutil.copyfile(source, destination)
        return source

    def export_csv(self):
        destination, _ = QFileDialog.getSaveFileName(
            self,
            "Xuất kết quả CSV",
            "ket_qua.csv",
            "CSV (*.csv)",
            options=QFileDialog.DontUseNativeDialog,
        )
        if destination:
            try:
                self.export_results_to(destination)
            except (OSError, ValueError) as error:
                self.notify("Không thể xuất CSV", str(error))

    def _error(self, message):
        self.result_badge.setText("ĐÁNH GIÁ THẤT BẠI")
        set_tone(self.result_badge, "error")
        self.result_note.setText("Không tạo được báo cáo mới. " + message)
        self.notify("Lỗi thực nghiệm", message)

    def _finished(self):
        self._enable_setup(True)

    def open_output(self):
        if self.last_output:
            QDesktopServices.openUrl(
                QUrl.fromLocalFile(str(Path(self.last_output).resolve()))
            )

    def add_session(self, mode, detector, log_path):
        row = self.sessions_table.rowCount()
        self.sessions_table.insertRow(row)
        values = [
            datetime.now().strftime("%H:%M:%S"),
            {"simulation": "Mô phỏng", "camera": "Camera", "video": "Video"}[mode],
            {"color": "Dấu màu", "aruco": "ArUco", "yolo": "YOLO Pose"}[detector]
            if mode != "simulation"
            else "Tổng hợp",
            "0",
            "Đang khởi động",
        ]
        for column, text in enumerate(values):
            item = QTableWidgetItem(text)
            item.setToolTip(log_path)
            self.sessions_table.setItem(row, column, item)
        self._refresh_session(row)
        return row

    def finish_session(self, row, count, error, log_path):
        self.sessions_table.item(row, 3).setText(str(count))
        self.sessions_table.item(row, 4).setText("Lỗi" if error else "Đã kết thúc")
        self.session_file.setText(log_path)
        self._refresh_session(row)

    def update_session(self, row, count):
        self.sessions_table.item(row, 3).setText(str(count))
        self.sessions_table.item(row, 4).setText("Đang phân tích")
        self._refresh_session(row)

    def _refresh_session(self, row):
        values = [self.sessions_table.item(row, col).text() for col in range(5)]
        if row >= self.session_list.count():
            self.session_list.addItem(QListWidgetItem())
        self.session_list.item(row).setText(
            f"{values[0]} · {values[1]}\n{values[3]} khung · {values[4]}"
        )
        self.session_list.item(row).setToolTip(
            values[2] + "\n" + self.sessions_table.item(row, 0).toolTip()
        )
        self.session_empty.hide()
        self.session_list.setMaximumHeight(
            min(220, max(84, self.session_list.count() * 76))
        )
        total = sum(
            int(self.sessions_table.item(index, 3).text())
            for index in range(self.sessions_table.rowCount())
        )
        self.history_summary.setText(
            f"{self.sessions_table.rowCount()} phiên · {total:,} khung"
        )
        if self.session_list.currentRow() < 0:
            self.session_list.setCurrentRow(row)
        if self.session_list.currentRow() == row:
            self._show_session_details(row)

    def _show_session_details(self, row):
        if row < 0 or row >= self.sessions_table.rowCount():
            self.copy_session_button.setEnabled(False)
            return
        values = [self.sessions_table.item(row, col).text() for col in range(5)]
        path = self.sessions_table.item(row, 0).toolTip()
        self.session_details.setText(
            f"Nguồn: {values[1]}\nNhận diện: {values[2]}\nBắt đầu: {values[0]}\nĐã nhận: {values[3]} khung\nTrạng thái: {values[4]}\nCSV: {Path(path).name}"
        )
        self.session_details.setToolTip(path)
        self.copy_session_button.setEnabled(bool(path))

    def _copy_session_path(self):
        row = self.session_list.currentRow()
        if row >= 0:
            QApplication.clipboard().setText(self.sessions_table.item(row, 0).toolTip())
