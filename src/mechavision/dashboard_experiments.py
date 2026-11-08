"""Giao diện thực nghiệm và lịch sử phiên của lần mở ứng dụng hiện tại."""
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QComboBox, QLineEdit,
    QPushButton, QDoubleSpinBox, QSpinBox, QStackedWidget, QSplitter, QTableWidgetItem,
)
from .dashboard_widgets import panel, text_label, badge, set_tone, table
from .dashboard_controller import EvaluationWorker
from .dashboard_monitoring import value_text

METHOD_LABELS = {'raw_cv_baseline': 'Thị giác trực tiếp', 'raw_visual': 'Thị giác trực tiếp',
                 'temporal_ekf': 'EKF thời gian', 'physics_ekf': 'EKF vật lý'}


class ExperimentsPage(QWidget):
    def __init__(self, browse, notify, geometry_path):
        super().__init__()
        self.browse = browse
        self.notify = notify
        self.geometry_path = geometry_path
        self.worker = None
        self.last_output = None
        self.last_result = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        setup, setup_layout = panel('THIẾT KẾ THỰC NGHIỆM')
        setup.setMinimumWidth(300)
        setup.setMaximumWidth(360)
        setup_layout.addWidget(text_label('Nguồn đánh giá', 'muted'))
        self.mode = QComboBox()
        self.mode.addItem('Dữ liệu mô phỏng', 'synthetic')
        self.mode.addItem('Quan sát đã ghi + tham chiếu', 'recorded')
        setup_layout.addWidget(self.mode)
        self.notice = text_label('Mô phỏng kiểm chứng luồng phần mềm, không chứng minh độ chính xác trên động cơ thực.', 'muted', True)
        setup_layout.addWidget(self.notice)
        self.inputs = QStackedWidget()
        synthetic = QWidget()
        grid = QGridLayout(synthetic)
        grid.setContentsMargins(0, 5, 0, 5)
        self.seconds = QDoubleSpinBox()
        self.seconds.setRange(1, 300)
        self.seconds.setValue(24)
        self.seconds.setSuffix(' s')
        self.fps = QSpinBox()
        self.fps.setRange(1, 120)
        self.fps.setValue(30)
        self.noise = QDoubleSpinBox()
        self.noise.setRange(0, 50)
        self.noise.setValue(3)
        self.noise.setSuffix(' px')
        self.seed = QSpinBox()
        self.seed.setRange(0, 2147483647)
        self.seed.setValue(42)
        for row, column, title, widget in [
            (0, 0, 'Thời lượng', self.seconds), (0, 1, 'Khung/giây', self.fps),
            (2, 0, 'Nhiễu quan sát', self.noise), (2, 1, 'Hạt giống', self.seed),
        ]:
            grid.addWidget(text_label(title, 'muted'), row, column)
            grid.addWidget(widget, row+1, column)
        self.inputs.addWidget(synthetic)
        recorded = QWidget()
        recorded_layout = QVBoxLayout(recorded)
        recorded_layout.setContentsMargins(0, 5, 0, 5)
        self.session_file = QLineEdit()
        self.truth_file = QLineEdit()
        self.geometry_file = QLineEdit()
        for title, widget, kind in [('CSV quan sát đã ghi', self.session_file, 'CSV (*.csv)'),
                                    ('CSV góc tham chiếu độc lập', self.truth_file, 'CSV (*.csv)'),
                                    ('Hình học đã hiệu chuẩn', self.geometry_file, 'JSON (*.json)')]:
            recorded_layout.addWidget(text_label(title, 'muted'))
            row = QHBoxLayout()
            row.addWidget(widget, 1)
            button = QPushButton('Chọn')
            button.clicked.connect(lambda checked=False, target=widget, file_filter=kind: self.browse(target, file_filter))
            row.addWidget(button)
            recorded_layout.addLayout(row)
        self.inputs.addWidget(recorded)
        setup_layout.addWidget(self.inputs)
        setup_layout.addWidget(text_label('Thư mục lưu kết quả', 'muted'))
        self.output_root = QLineEdit('outputs/experiments')
        setup_layout.addWidget(self.output_root)
        setup_layout.addWidget(text_label('Mỗi lần chạy tạo thư mục riêng. Ba phương pháp dùng cùng quan sát và giữ nguyên tham số đánh giá.', 'muted', True))
        self.run_button = QPushButton('Chạy đánh giá')
        self.run_button.setObjectName('primary')
        self.run_button.clicked.connect(self.run_evaluation)
        setup_layout.addWidget(self.run_button)
        setup_layout.addStretch()
        setup_layout.addWidget(text_label('Lưu ý nghiên cứu', 'panel_title'))
        setup_layout.addWidget(text_label('Góc tham chiếu phải được đo độc lập. Sai số theo chu kỳ 360° không kiểm chứng số vòng quay liên tục.', 'muted', True))
        layout.addWidget(setup)

        right = QSplitter(Qt.Vertical)
        right.setChildrenCollapsible(False)
        right.setHandleWidth(10)
        self.result_badge = badge('CHƯA CÓ BÁO CÁO', 'muted')
        result, result_layout = panel('SO SÁNH THUẬT TOÁN', trailing=self.result_badge)
        self.result_note = text_label('Chạy một thực nghiệm để xem kết quả. Chưa có số liệu được tạo hoặc nạp.', 'muted', True)
        result_layout.addWidget(self.result_note)
        self.results_table = table(['Phương pháp', 'MAE (°)', 'RMSE (°)', 'P95 (°)', 'Bao phủ (%)'])
        result_layout.addWidget(self.results_table, 1)
        self.output_label = text_label('Chưa có tệp kết quả', 'muted', True)
        self.output_label.setTextInteractionFlags(Qt.TextSelectableByMouse)
        result_layout.addWidget(self.output_label)
        self.open_button = QPushButton('Mở thư mục kết quả')
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_output)
        result_layout.addWidget(self.open_button, 0, Qt.AlignRight)
        right.addWidget(result)
        history, history_layout = panel('NHẬT KÝ PHIÊN', 'Các phiên thực sự đã khởi chạy trong lần mở ứng dụng này.')
        self.sessions_table = table(['Bắt đầu', 'Nguồn', 'Nhận diện', 'Số khung', 'Trạng thái'])
        history_layout.addWidget(self.sessions_table, 1)
        right.addWidget(history)
        right.setSizes([380, 220])
        layout.addWidget(right, 1)
        self.mode.currentIndexChanged.connect(self._mode_changed)

    @property
    def busy(self):
        return self.worker is not None and self.worker.isRunning()

    def _mode_changed(self, index):
        self.inputs.setCurrentIndex(index)
        self.notice.setText('Mô phỏng kiểm chứng luồng phần mềm, không chứng minh độ chính xác trên động cơ thực.' if index == 0 else
                            'Dùng cùng CSV quan sát cho ba bộ ước lượng. Người thực nghiệm phải xác minh nguồn video và tính độc lập của tham chiếu.')
        if index == 1 and not self.geometry_file.text():
            self.geometry_file.setText(self.geometry_path())

    def run_evaluation(self):
        if self.busy:
            return
        mode = self.mode.currentData()
        if mode == 'synthetic':
            parameters = dict(seconds=self.seconds.value(), fps=self.fps.value(),
                              seed=self.seed.value(), noise_px=self.noise.value())
        else:
            parameters = dict(session_file=self.session_file.text().strip(), truth_file=self.truth_file.text().strip(),
                              geometry_file=self.geometry_file.text().strip())
            if not all(Path(value).is_file() for value in parameters.values()):
                self.notify('Thiếu dữ liệu thực nghiệm', 'Hãy chọn CSV quan sát, CSV góc tham chiếu và JSON hình học hiện có.')
                return
        if not self.output_root.text().strip():
            self.notify('Thiếu thư mục kết quả', 'Hãy nhập thư mục để lưu kết quả đánh giá.')
            return
        output = Path(self.output_root.text().strip()) / datetime.now().strftime('run_%Y%m%d_%H%M%S_%f')
        self.worker = EvaluationWorker(mode, parameters, str(output))
        self.worker.completed.connect(lambda report, path, source=mode: self._show_result(report, path, source))
        self.worker.failed.connect(self._error)
        self.worker.finished.connect(self._finished)
        self._enable_setup(False)
        self.results_table.setRowCount(0)
        self.open_button.setEnabled(False)
        self.last_output = None
        self.last_result = None
        self.output_label.setText('Chưa có báo cáo cho lần chạy này.')
        self.result_badge.setText('ĐANG ĐÁNH GIÁ')
        set_tone(self.result_badge, 'warning')
        self.result_note.setText('Đang chạy quy trình đánh giá. Giao diện giám sát vẫn có thể sử dụng.')
        self.worker.start()

    def _enable_setup(self, enabled):
        for widget in (self.mode, self.inputs, self.output_root, self.run_button):
            widget.setEnabled(enabled)

    def _show_result(self, report, path, source):
        self.last_result, self.last_output = report, path
        self.results_table.setRowCount(0)
        for name, values in report['methods'].items():
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            cells = [METHOD_LABELS.get(name, name), value_text(values.get('mae_deg'), 3),
                     value_text(values.get('rmse_deg'), 3), value_text(values.get('p95_abs_error_deg'), 3),
                     value_text(values.get('coverage_pct', values.get('availability_pct')), 2)]
            for column, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setToolTip(text)
                self.results_table.setItem(row, column, item)
        self.result_badge.setText('MÔ PHỎNG' if source == 'synthetic' else 'QUAN SÁT ĐÃ GHI')
        set_tone(self.result_badge, 'warning' if source == 'synthetic' else 'data')
        self.result_note.setText('Kết quả mô phỏng • Không phải kết quả đo động cơ thực.' if source == 'synthetic' else
                                 'Kết quả đối chiếu CSV • Chỉ áp dụng cho khung có tham chiếu; chưa xác minh độc lập phần cứng.')
        self.output_label.setText('Đã lưu JSON và CSV: '+str(Path(path).resolve()))
        self.open_button.setEnabled(True)

    def _error(self, message):
        self.result_badge.setText('ĐÁNH GIÁ THẤT BẠI')
        set_tone(self.result_badge, 'error')
        self.result_note.setText('Không tạo được báo cáo mới. '+message)
        self.notify('Lỗi thực nghiệm', message)

    def _finished(self):
        self._enable_setup(True)

    def open_output(self):
        if self.last_output:
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(Path(self.last_output).resolve())))

    def add_session(self, mode, detector, log_path):
        row = self.sessions_table.rowCount()
        self.sessions_table.insertRow(row)
        values = [datetime.now().strftime('%H:%M:%S'),
                  {'simulation': 'Mô phỏng', 'camera': 'Camera', 'video': 'Video'}[mode],
                  {'color': 'Dấu màu', 'aruco': 'ArUco', 'yolo': 'YOLO Pose'}[detector] if mode != 'simulation' else 'Tổng hợp',
                  '0', 'Đang khởi động']
        for column, text in enumerate(values):
            item = QTableWidgetItem(text)
            item.setToolTip(log_path)
            self.sessions_table.setItem(row, column, item)
        return row

    def finish_session(self, row, count, error, log_path):
        self.sessions_table.item(row, 3).setText(str(count))
        self.sessions_table.item(row, 4).setText('Lỗi' if error else 'Đã kết thúc')
        self.session_file.setText(log_path)

    def update_session(self, row, count):
        self.sessions_table.item(row, 3).setText(str(count))
        self.sessions_table.item(row, 4).setText('Đang phân tích')
