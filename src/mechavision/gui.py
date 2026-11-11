"""Dashboard V2: phối hợp các trang, controller nền và trạng thái hiển thị."""

from datetime import datetime
from pathlib import Path
from PySide6.QtCore import Qt, QLocale
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QFileDialog,
    QMessageBox,
    QFrame,
)
from .dashboard_theme import STYLE, apply_application_theme
from .dashboard_shell import DashboardShell
from .dashboard_state import DashboardState
from .dashboard_controller import Worker
from .dashboard_monitoring import MonitoringPage, SOURCE_LABELS
from .dashboard_analytics import AnalyticsPage
from .dashboard_settings import SettingsPage
from .dashboard_experiments import ExperimentsPage
from .dashboard_widgets import set_tone
from .qt_support import _VietnameseQtTranslator, _VietnameseExportDialog, _message
from .qt_support import _Utf8CSVExporter as _Utf8CSVExporter
from .geometry import Geometry
from .i18n import _font


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        app = QApplication.instance()
        apply_application_theme(app)
        font_path = Path(_font(12).path)
        for sibling in ("seguisb.ttf", "segoeuib.ttf"):
            if font_path.with_name(sibling).is_file():
                QFontDatabase.addApplicationFont(str(font_path.with_name(sibling)))
        font_id = QFontDatabase.addApplicationFont(str(font_path))
        if font_id >= 0:
            app.setFont(QFont(QFontDatabase.applicationFontFamilies(font_id)[0], 10))
        if not hasattr(app, "_mechavision_translator"):
            app._mechavision_translator = _VietnameseQtTranslator(app)
            app.installTranslator(app._mechavision_translator)
        QLocale.setDefault(QLocale("vi_VN"))
        self.setWindowTitle("MechaVision AI — Ultimate Premium V4")
        self.setMinimumSize(1180, 680)
        available = self.screen().availableGeometry()
        self.resize(
            min(1600, max(1180, available.width() - 40)),
            min(960, max(680, available.height() - 60)),
        )
        self.setStyleSheet(STYLE)
        self.worker = None
        self._raw_frame = None
        self.state = DashboardState()
        self._session_row = None
        self._build()

    def _build(self):
        self.shell = DashboardShell()
        self.setCentralWidget(self.shell)
        self.monitor = MonitoringPage()
        header = self.shell.findChild(QFrame, "station_header")
        header.layout().insertWidget(3, self.monitor.tracking_badge)
        self.monitor.tracking_badge.show()
        self.analysis = AnalyticsPage()
        self.settings = SettingsPage(self._browse)
        self.experiments = ExperimentsPage(
            self._browse, self._notify, lambda: self.settings.geom_path.text()
        )
        for page in (self.monitor, self.analysis, self.experiments, self.settings):
            self.shell.stack.addWidget(page)
        self.shell.nav_group.idClicked.connect(self.navigate)
        self.shell.configure_btn.clicked.connect(lambda: self.navigate(3))
        self.shell.start_btn.clicked.connect(self.start)
        self.shell.stop_btn.clicked.connect(self.stop)
        self.start_btn, self.stop_btn = self.shell.start_btn, self.shell.stop_btn
        self.source_mode, self.detector_mode = (
            self.settings.source_mode,
            self.settings.detector_mode,
        )
        self.input_source, self.geom_path = (
            self.settings.input_source,
            self.settings.geom_path,
        )
        self.weights_path = self.settings.weights_path
        self.banner, self.confidence_label = (
            self.monitor.banner,
            self.monitor.confidence_label,
        )
        self.camera_label, self.twin_label = self.monitor.camera, self.monitor.twin
        self.session_text = self.shell.session_text
        kpi = self.monitor.kpis.labels
        self.angle_label, self.rpm_label = kpi["angle"], kpi["rpm"]
        self.sigma_label, self.resid_label = kpi["sigma"], kpi["discrepancy"]
        self.fps_label, self.state_label = kpi["fps"], kpi["state"]
        self.angle_plot = self.analysis.angle_plot
        self.angle_raw_curve = self.analysis.curves["raw_angle"]
        self.angle_ekf_curve = self.analysis.curves["physics_angle"]
        self.timestamps = self.state.series["time"]
        self.angles_raw, self.angles_est = (
            self.state.series["raw_angle"],
            self.state.series["physics_angle"],
        )
        self.piston_meas, self.piston_pred = (
            self.state.series["piston_observed"],
            self.state.series["piston_estimated"],
        )
        self.fps_series = self.state.series["fps"]
        for plot in [self.monitor.overview, *self.analysis.plots]:
            dialog = _VietnameseExportDialog(plot.scene())
            dialog.setParent(self, Qt.Window)
            plot.scene().exportDialog = dialog
        self.analysis.time_window.currentIndexChanged.connect(
            lambda: self.analysis.update_state(self.state)
        )
        self.analysis.follow_check.toggled.connect(
            lambda: self.analysis.update_state(self.state)
        )
        self.source_mode.currentIndexChanged.connect(self._update_source_badge)
        self._update_source_badge()
        self.settings.visualization_changed.connect(self._visualization_preference)
        self.monitor.annotation_button.toggled.connect(
            self.settings.annotation_check.setChecked
        )
        self.monitor.focus_button.toggled.connect(self.settings.focus_check.setChecked)
        self.navigate(0)

    def _visualization_preference(self, name, enabled):
        if name == "annotations":
            self.monitor.annotation_button.setChecked(enabled)
        elif name == "focus":
            self.monitor.focus_button.setChecked(enabled)

    def navigate(self, index):
        self.shell.select_page(index)
        if index == 1:
            self.analysis.update_state(self.state)

    def _notify(self, title, text):
        _message(self, title, text)

    def _browse(self, widget, filter, directory=False):
        dialog = QFileDialog(self, "Chọn thư mục" if directory else "Chọn tệp")
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(
            QFileDialog.Directory if directory else QFileDialog.ExistingFile
        )
        if directory:
            dialog.setOption(QFileDialog.ShowDirsOnly)
        else:
            dialog.setNameFilters(filter.split(";;"))
        for role, text in [
            (QFileDialog.LookIn, "Thư mục:"),
            (QFileDialog.FileName, "Tên tệp:"),
            (QFileDialog.FileType, "Loại tệp:"),
            (QFileDialog.Accept, "Chọn" if directory else "Mở"),
            (QFileDialog.Reject, "Hủy"),
        ]:
            dialog.setLabelText(role, text)
        if dialog.exec():
            widget.setText(dialog.selectedFiles()[0])

    def _update_source_badge(self):
        if self.worker and self.worker.isRunning():
            return
        mode = self.source_mode.currentData()
        self.shell.source_badge.setText("TIẾP: " + SOURCE_LABELS[mode])
        self.shell.source_badge.setToolTip(
            "Nguồn được dùng cho phiên kế tiếp. Nguồn của dữ liệu đã hiển thị được ghi ở trang Giám sát."
        )
        set_tone(self.shell.source_badge, "warning" if mode == "simulation" else "data")

    def start(self):
        if self.worker and self.worker.isRunning():
            return
        mode = self.source_mode.currentData()
        geometry = self.geom_path.text().strip()
        source = self.input_source.text().strip()
        if mode != "simulation":
            if not Path(geometry).is_file():
                self._notify(
                    "Cần hiệu chuẩn",
                    "Phép đo camera/video cần tệp JSON hình học đã hiệu chuẩn. Hãy chọn cấu hình trong Cài đặt.",
                )
                return
            try:
                selected_geometry = Geometry.from_json(geometry)
            except (OSError, ValueError, TypeError) as error:
                self._notify("Hình học không hợp lệ", str(error))
                return
            if (
                self.detector_mode.currentData() == "yolo"
                and not Path(self.weights_path.text()).is_file()
            ):
                self._notify(
                    "Cần trọng số YOLO",
                    "Hãy chọn trọng số mô hình ba điểm đã huấn luyện hoặc dùng dấu màu/ArUco.",
                )
                return
            if mode == "camera" and not source.isdigit():
                self._notify("Camera", "Nguồn camera phải là số nguyên (0, 1, …).")
                return
            if mode == "video" and not Path(source).is_file():
                self._notify("Video", "Hãy chọn một tệp video hiện có.")
                return
        if not self.settings.output_dir.text().strip():
            self._notify(
                "Thiếu thư mục nhật ký", "Hãy chọn thư mục lưu CSV trong Cài đặt."
            )
            return
        filename = str(
            Path(self.settings.output_dir.text().strip())
            / datetime.now().strftime("session_%Y%m%d_%H%M%S_%f.csv")
        )
        self.state.reset(mode, filename)
        self.state.phase = "connecting"
        self.monitor.set_geometry(
            Geometry() if mode == "simulation" else selected_geometry
        )
        self._raw_frame = None
        self.monitor.prepare(mode)
        self.shell.update_session(self.state)
        self.analysis.clear()
        self.settings.set_locked(True)
        self._session_row = self.experiments.add_session(
            mode, self.detector_mode.currentData(), filename
        )
        self.worker = Worker(
            mode,
            source,
            self.detector_mode.currentData(),
            self.weights_path.text().strip() or None,
            geometry,
            filename,
            self.settings.device.text().strip() or "cpu",
        )
        worker = self.worker
        worker.raw_frame.connect(
            lambda frame: (
                setattr(self, "_raw_frame", frame) if self.worker is worker else None
            )
        )
        worker.sample.connect(
            lambda frame, twin, data: (
                self._on_sample(frame, twin, data) if self.worker is worker else None
            )
        )
        worker.failed.connect(
            lambda message: self._on_error(message) if self.worker is worker else None
        )
        worker.ended.connect(lambda: self._on_end() if self.worker is worker else None)
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.session_text.setText("Nhật ký CSV → " + filename)
        self.session_text.setToolTip(str(Path(filename).resolve()))
        self.shell.system_badge.setText(
            "ĐANG KẾT NỐI" if mode == "camera" else "ĐANG KHỞI ĐỘNG"
        )
        set_tone(self.shell.system_badge, "warning")
        self.shell.sidebar_status.setText("PHIÊN ĐANG CHẠY")
        self.shell.source_badge.setText(SOURCE_LABELS[mode])
        worker.start()

    def stop(self):
        if self.worker and self.worker.isRunning():
            self.state.phase = "stopping"
            self.worker.stop()
            self.shell.system_badge.setText("ĐANG DỪNG")
            set_tone(self.shell.system_badge, "warning")
        self.stop_btn.setEnabled(False)

    def _on_sample(self, frame, twin, data):
        if self.state.phase not in ("stopping", "error"):
            self.state.phase = "running"
            self.shell.system_badge.setText("ĐANG PHÂN TÍCH")
            set_tone(self.shell.system_badge, "valid")
        self.state.append(data["observation"], data["metrics"])
        self.analysis.record_observation(self.state)
        self.shell.update_session(self.state)
        if self._session_row is not None:
            self.experiments.update_session(self._session_row, self.state.sample_count)
        self.monitor.update_state(self.state, frame, twin, self._raw_frame)
        if self.shell.stack.currentIndex() == 1 and (
            self.state.sample_count % 3 == 0 or self.state.sample_count == 1
        ):
            self.analysis.update_state(self.state)

    def _on_error(self, message):
        self.monitor.add_event("Lỗi nguồn · " + message)
        self.state.error = message
        self.state.phase = "error"
        self.banner.setText(
            "Lỗi nguồn dữ liệu • Không thể tiếp tục phiên. Hãy kiểm tra Cài đặt."
        )
        self.banner.setToolTip(message)
        self.monitor.tracking_badge.setText("LỖI")
        set_tone(self.monitor.tracking_badge, "error")
        self.shell.system_badge.setText("LỖI PHIÊN")
        set_tone(self.shell.system_badge, "error")
        self._notify("Lỗi MechaVision", "Không thể hoàn tất phiên xử lý.\n" + message)

    def _on_end(self):
        self.monitor.add_event(
            "Kết thúc phiên · " + str(self.state.sample_count) + " khung"
        )
        self.state.phase = "error" if self.state.error else "stopped"
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.settings.set_locked(False)
        self.shell.system_badge.setText("PHIÊN LỖI" if self.state.error else "ĐÃ DỪNG")
        set_tone(self.shell.system_badge, "error" if self.state.error else "muted")
        self.shell.sidebar_status.setText("KHÔNG THU NHẬN")
        if not self.state.error:
            self.banner.setText(
                SOURCE_LABELS[self.state.mode]
                + " • Phiên đã kết thúc; đang xem mẫu cuối cùng."
            )
            self.monitor.tracking_badge.setText("ĐÃ DỪNG")
            set_tone(self.monitor.tracking_badge, "muted")
        self.confidence_label.setText(
            "Không có dữ liệu mới. Các giá trị còn hiển thị thuộc mẫu cuối của phiên đã dừng."
        )
        self.session_text.setText(
            "Đã lưu phiên → " + self.state.log_path
            if self.state.sample_count
            else "Phiên kết thúc trước khi nhận được dữ liệu."
        )
        if self._session_row is not None:
            self.experiments.finish_session(
                self._session_row,
                self.state.sample_count,
                bool(self.state.error),
                self.state.log_path,
            )
        self.analysis.update_state(self.state)
        self.shell.update_session(self.state)

    def _render_image(self, label, frame):
        label.set_frame(frame)

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.stop()
            if not self.worker.wait(3500):
                event.ignore()
                _message(
                    self,
                    "Đang dừng",
                    "Nguồn camera đang dừng. Vui lòng thử đóng lại sau.",
                    QMessageBox.Information,
                )
                return
        if self.experiments.busy and not self.experiments.worker.wait(3500):
            event.ignore()
            _message(
                self,
                "Đang đánh giá",
                "Thực nghiệm vẫn đang chạy. Hãy chờ hoàn tất trước khi đóng ứng dụng.",
                QMessageBox.Information,
            )
            return
        event.accept()


def launch():
    import sys

    app = QApplication.instance() or QApplication(sys.argv)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
