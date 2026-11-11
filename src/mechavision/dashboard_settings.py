"""Cấu hình theo nhóm; điều khiển thật và giới hạn hỗ trợ được ghi rõ."""

from pathlib import Path
from inspect import signature
from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QScrollArea,
    QTabWidget,
    QCheckBox,
    QButtonGroup,
    QFrame,
)
from .dashboard_widgets import panel, text_label, badge, set_tone
from .geometry import Geometry
from .estimators import MotionEKF


class SettingsPage(QScrollArea):
    visualization_changed = Signal(str, bool)

    def __init__(self, browse):
        super().__init__()
        self.setWidgetResizable(True)
        self.browse = browse
        self.locked = False
        self._last_mode = "simulation"
        self._sources = {"camera": "0", "video": ""}
        body = QWidget()
        body.setObjectName("shell")
        self.setWidget(body)
        layout = QVBoxLayout(body)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        heading = QHBoxLayout()
        heading.addWidget(text_label("CẤU HÌNH HỆ THỐNG", "panel_title"))
        heading.addStretch()
        heading.addWidget(badge("ÁP DỤNG CHO PHIÊN MỚI", "data"))
        layout.addLayout(heading)
        layout.addWidget(
            text_label(
                "Nguồn và mô hình được khóa khi đang thu nhận. Tùy chọn hiển thị áp dụng ngay, không tác động phép đo.",
                "muted",
                True,
            )
        )
        self.tabs = QTabWidget()
        self.tabs.setObjectName("research_tabs")
        self.tabs.tabBar().hide()
        workspace = QHBoxLayout()
        workspace.setSpacing(16)
        rail = QFrame()
        rail.setFixedWidth(200)
        rail.setObjectName("panel")
        navigation = QVBoxLayout(rail)
        navigation.setContentsMargins(12, 16, 12, 16)
        navigation.addWidget(text_label("NHÓM CẤU HÌNH", "eyebrow"))
        self.group_buttons = []
        self.group_nav = QButtonGroup(self)
        for index, (title, hint) in enumerate(
            [
                ("Nguồn và nhận diện", "Camera · Video · YOLO"),
                ("Hình học và EKF", "Hiệu chuẩn · Bộ lọc"),
                ("Hiển thị và lưu trữ", "Vùng nhìn · Nhật ký CSV"),
            ]
        ):
            button = QPushButton(title)
            button.setObjectName("nav")
            button.setCheckable(True)
            button.setToolTip(hint)
            navigation.addWidget(button)
            description = text_label(hint, "micro", True)
            navigation.addWidget(description)
            navigation.addSpacing(12)
            self.group_nav.addButton(button, index)
            self.group_buttons.append(button)
        navigation.addStretch()
        navigation.addWidget(
            text_label(
                "Thông số nguồn áp dụng cho phiên kế tiếp. Dừng phiên để thay đổi.",
                "muted",
                True,
            )
        )
        self.group_nav.idClicked.connect(self.tabs.setCurrentIndex)
        self.tabs.currentChanged.connect(
            lambda index: self.group_buttons[index].setChecked(True)
        )
        self.group_buttons[0].setChecked(True)
        workspace.addWidget(rail)
        workspace.addWidget(self.tabs, 1)
        layout.addLayout(workspace, 1)
        summary, summary_layout = panel("Cấu hình cho phiên kế tiếp")
        self.config_summary = text_label("", "muted", True)
        self.config_summary.setStyleSheet("font-size:13px; color:#CAD8E8;")
        summary_layout.addWidget(self.config_summary)
        self.activation_note = text_label("", "muted", True)
        summary_layout.addWidget(self.activation_note)
        layout.addWidget(summary)

        acquisition = QWidget()
        columns = QHBoxLayout(acquisition)
        columns.setContentsMargins(0, 0, 0, 0)
        columns.setAlignment(Qt.AlignTop)
        columns.setSpacing(16)
        self.source_card, source_layout = panel(
            "01 / NGUỒN THU NHẬN", "Chọn nguồn của phiên đo và đường dẫn thu nhận."
        )
        source_form = QFormLayout()
        source_form.setSpacing(14)
        source_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.source_mode = QComboBox()
        for title, value in [
            ("Mô phỏng", "simulation"),
            ("Camera trực tiếp", "camera"),
            ("Video đã ghi", "video"),
        ]:
            self.source_mode.addItem(title, value)
        source_form.addRow("Loại nguồn", self.source_mode)
        self.input_source = QLineEdit("0")
        source_form.addRow("Camera / video", self.input_source)
        self.video_button = QPushButton("Chọn tệp video")
        self.video_button.clicked.connect(
            lambda: browse(
                self.input_source, "Video (*.mp4 *.avi *.mov *.mkv);;Tất cả tệp (*)"
            )
        )
        source_form.addRow("", self.video_button)
        source_layout.addLayout(source_form)
        self.source_hint = text_label("", "muted", True)
        source_layout.addWidget(self.source_hint)
        source_layout.addSpacing(16)
        source_layout.addWidget(text_label("MÔ PHỎNG / VIDEO / CAMERA", "eyebrow"))
        source_layout.addWidget(
            text_label(
                "Nhãn nguồn luôn được giữ riêng với trạng thái theo dõi. Một tệp video không tự chứng minh kết quả thực nghiệm vật lý.",
                "muted",
                True,
            )
        )
        columns.addWidget(self.source_card, 1)
        self.model_card, model_layout = panel(
            "02 / NHẬN DIỆN & THIẾT BỊ",
            "Bộ nhận diện dùng đúng ba điểm đặc trưng của cơ cấu.",
        )
        model_form = QFormLayout()
        model_form.setSpacing(14)
        model_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.detector_mode = QComboBox()
        for title, value in [
            ("Dấu màu", "color"),
            ("Dấu ArUco", "aruco"),
            ("YOLO Pose", "yolo"),
        ]:
            self.detector_mode.addItem(title, value)
        model_form.addRow("Bộ nhận diện", self.detector_mode)
        self.weights_path = QLineEdit()
        self.weights_path.setPlaceholderText("Trọng số YOLO Pose (.pt)")
        model_form.addRow("Trọng số", self.weights_path)
        self.weights_button = QPushButton("Chọn trọng số")
        self.weights_button.clicked.connect(
            lambda: browse(self.weights_path, "PyTorch (*.pt)")
        )
        model_form.addRow("", self.weights_button)
        self.device = QLineEdit("cpu")
        self.device.setToolTip(
            "Thiết bị YOLO: cpu hoặc chỉ số GPU, ví dụ 0. Áp dụng cho phiên mới."
        )
        model_form.addRow("Thiết bị YOLO", self.device)
        model_layout.addLayout(model_form)
        model_layout.addWidget(
            text_label(
                "Trọng số LEGO riêng chưa được cung cấp. Không hiển thị mức độ chính xác khi chưa có dữ liệu đánh giá độc lập.",
                "muted",
                True,
            )
        )
        model_layout.addSpacing(16)
        model_layout.addWidget(badge("SUY LUẬN CHẠY TRÊN WORKER", "data"))
        columns.addWidget(self.model_card, 1)
        self.tabs.addTab(acquisition, "Nguồn / nhận diện")

        geometry_page = QWidget()
        geometry_columns = QHBoxLayout(geometry_page)
        geometry_columns.setContentsMargins(0, 0, 0, 0)
        geometry_columns.setAlignment(Qt.AlignTop)
        geometry_columns.setSpacing(16)
        geometry_card, geometry_layout = panel(
            "03 / HÌNH HỌC HIỆU CHUẨN",
            "Đơn vị pixel; giữ đúng vị trí khớp vật lý và mặt phẳng chuyển động.",
        )
        self.geom_path = QLineEdit("configs/geometry.example.json")
        geometry_layout.addWidget(self.geom_path)
        self.geometry_button = QPushButton("Chọn cấu hình hình học")
        self.geometry_button.clicked.connect(
            lambda: (browse(self.geom_path, "JSON (*.json)"), self.preview_geometry())
        )
        geometry_layout.addWidget(self.geometry_button)
        self.geometry_badge = badge("CẤU HÌNH MẪU", "warning")
        geometry_layout.addWidget(self.geometry_badge)
        self.geometry_summary = text_label("", "muted", True)
        geometry_layout.addWidget(self.geometry_summary)
        geometry_layout.addSpacing(16)
        geometry_layout.addWidget(text_label("TRƯỚC KHI ĐO CƠ CẤU THỰC", "panel_title"))
        geometry_layout.addWidget(
            text_label(
                "01  Gá camera cố định, gần vuông góc với mặt phẳng cơ cấu.\n02  Chọn tâm quay, chốt khuỷu và khớp thanh truyền–pít-tông.\n03  Đo và xác minh cấu hình trên cơ cấu riêng.",
                "muted",
                True,
            )
        )
        geometry_columns.addWidget(geometry_card, 1)
        ekf_card, ekf_layout = panel(
            "04 / BỘ ƯỚC LƯỢNG EKF",
            "Giá trị mặc định được đọc từ bộ lọc hiện có. UI chưa hỗ trợ sửa tham số EKF.",
        )
        ekf_layout.addWidget(badge("CHỈ ĐỌC · KHÔNG ĐỔI THUẬT TOÁN", "muted"))
        defaults = signature(MotionEKF.__init__).parameters
        ekf_form = QFormLayout()
        ekf_form.setSpacing(16)
        self.ekf_defaults = {}
        for key, title, unit in [
            ("measurement_sigma_px", "Nhiễu phép đo σ", "px"),
            ("accel_sigma", "Nhiễu gia tốc σ", "rad/s²"),
            ("max_prediction_sec", "Thời gian dự báo tối đa", "s"),
            ("max_sigma_deg", "Độ bất định giới hạn", "°"),
            ("gate_sigma", "Cổng loại ngoại lai", "σ"),
        ]:
            value = defaults[key].default
            self.ekf_defaults[key] = value
            ekf_form.addRow(title, text_label(f"{value:g} {unit}", "session_value"))
        ekf_layout.addLayout(ekf_form)
        ekf_layout.addSpacing(16)
        ekf_layout.addWidget(
            text_label(
                "Trạng thái nội bộ dùng radian và rad/s. Cả EKF thời gian và EKF vật lý giữ nguyên quy trình cập nhật hiện có.",
                "muted",
                True,
            )
        )
        geometry_columns.addWidget(ekf_card, 1)
        self.tabs.addTab(geometry_page, "Hình học / EKF")

        presentation = QWidget()
        presentation_layout = QVBoxLayout(presentation)
        presentation_layout.setContentsMargins(0, 12, 0, 0)
        row = QHBoxLayout()
        view_card, view_layout = panel(
            "05 / HIỂN THỊ",
            "Tùy chọn chỉ tác động viewport, không thay đổi khung gốc hoặc dữ liệu ghi.",
        )
        self.annotation_check = QCheckBox("Hiển thị chú thích và điểm đặc trưng")
        self.annotation_check.setChecked(True)
        self.focus_check = QCheckBox("Cận cảnh theo hình học hiệu chuẩn")
        self.focus_check.setChecked(True)
        self.annotation_check.toggled.connect(
            lambda value: self.visualization_changed.emit("annotations", value)
        )
        self.focus_check.toggled.connect(
            lambda value: self.visualization_changed.emit("focus", value)
        )
        view_layout.addWidget(self.annotation_check)
        view_layout.addWidget(self.focus_check)
        view_layout.addSpacing(16)
        row.addWidget(view_card, 1)
        performance, performance_layout = panel(
            "06 / HIỆU NĂNG", "Thiết bị suy luận được chọn ở nhóm Nguồn / nhận diện."
        )
        performance_layout.addWidget(
            text_label(
                "Bộ đệm biểu đồ: tối đa 3.600 mẫu\nLuồng thu nhận / ước lượng: worker nền\nGiới hạn FPS / batch inference: chưa hỗ trợ chỉnh trong UI\nĐộ trễ toàn trình / VRAM: chưa có phép đo",
                "muted",
                True,
            )
        )
        performance_layout.addSpacing(16)
        row.addWidget(performance, 1)
        presentation_layout.addLayout(row)
        self.logging_card, log_layout = panel(
            "07 / LƯU TRỮ PHIÊN",
            "CSV lưu phép đo và kết quả gốc; phép đo thiếu được để trống.",
        )
        log_row = QHBoxLayout()
        self.output_dir = QLineEdit("outputs")
        log_row.addWidget(self.output_dir, 1)
        self.output_button = QPushButton("Chọn thư mục")
        self.output_button.clicked.connect(
            lambda: browse(self.output_dir, "", directory=True)
        )
        log_row.addWidget(self.output_button)
        log_layout.addLayout(log_row)
        log_layout.addWidget(
            text_label(
                "Mỗi phiên có tệp riêng. Không tự tạo góc tham chiếu thực hoặc thay thế giá trị thiếu bằng số không.",
                "muted",
                True,
            )
        )
        presentation_layout.addWidget(self.logging_card)
        presentation_layout.addStretch()
        self.tabs.addTab(presentation, "Hiển thị / lưu trữ")
        self.source_mode.currentIndexChanged.connect(self._source_changed)
        self.detector_mode.currentIndexChanged.connect(self.apply_availability)
        self.geom_path.editingFinished.connect(self.preview_geometry)
        self.apply_availability()
        self.preview_geometry()
        for field in (
            self.input_source,
            self.weights_path,
            self.device,
            self.geom_path,
            self.output_dir,
        ):
            field.textChanged.connect(self._refresh_summary)
        self._refresh_summary()

    def _refresh_summary(self):
        mode = self.source_mode.currentData()
        detector = (
            self.detector_mode.currentText()
            if mode != "simulation"
            else "Bộ mô phỏng tổng hợp"
        )
        source = self.input_source.text() if mode != "simulation" else "Mô phỏng nội bộ"
        geometry = (
            Path(self.geom_path.text()).name
            if mode != "simulation"
            else "Hình học mặc định của Simulator"
        )
        weights = (
            Path(self.weights_path.text()).name
            if self.weights_path.text().strip()
            else "Chưa chọn trọng số"
        )
        self.config_summary.setText(
            f"Nguồn: {self.source_mode.currentText()} · {Path(source).name}\nNhận diện: {detector} · Hình học: {geometry}\nNhật ký: {self.output_dir.text()}"
        )
        self.config_summary.setToolTip(
            f"Nguồn: {source}\nTrọng số: {weights}\nHình học: {self.geom_path.text()}\nThiết bị: {self.device.text()}"
        )
        reason = (
            "Đang thu nhận: dừng phiên để sửa nguồn, mô hình và nơi lưu."
            if self.locked
            else "Mô phỏng: camera, detector, hình học ngoài và YOLO không được dùng."
            if mode == "simulation"
            else "Trọng số và thiết bị chỉ được kích hoạt khi chọn YOLO Pose. Chọn Video để bật nút chọn tệp."
        )
        self.activation_note.setText(
            reason + " Tùy chọn hiển thị áp dụng ngay; tham số EKF chỉ đọc."
        )
        for widget in (
            self.input_source,
            self.video_button,
            self.detector_mode,
            self.weights_path,
            self.weights_button,
            self.device,
            self.geom_path,
            self.geometry_button,
        ):
            widget.setToolTip(
                reason
                if not widget.isEnabled()
                else "Áp dụng cho phiên kế tiếp. "
                + (
                    "Thiết bị YOLO: cpu hoặc chỉ số GPU, ví dụ 0."
                    if widget is self.device
                    else ""
                )
            )

    def _source_changed(self):
        if self._last_mode in self._sources:
            self._sources[self._last_mode] = self.input_source.text()
        mode = self.source_mode.currentData()
        if mode in self._sources:
            self.input_source.setText(self._sources[mode])
        self._last_mode = mode
        self.apply_availability()

    def apply_availability(self):
        mode = self.source_mode.currentData()
        live = mode != "simulation"
        yolo = live and self.detector_mode.currentData() == "yolo"
        self.source_mode.setEnabled(not self.locked)
        self.input_source.setEnabled(live and not self.locked)
        self.input_source.setPlaceholderText(
            "Số hiệu camera, ví dụ 0" if mode == "camera" else "Đường dẫn video đã ghi"
        )
        self.video_button.setEnabled(mode == "video" and not self.locked)
        self.detector_mode.setEnabled(live and not self.locked)
        for widget in (self.weights_path, self.weights_button, self.device):
            widget.setEnabled(yolo and not self.locked)
        for widget in (self.geom_path, self.geometry_button):
            widget.setEnabled(live and not self.locked)
        for widget in (self.output_dir, self.output_button):
            widget.setEnabled(not self.locked)
        self.source_hint.setText(
            {
                "simulation": "Mô phỏng dùng tham số mặc định của Simulator. Detector, trọng số và tệp hình học ngoài không được dùng.",
                "camera": "Camera trực tiếp cần hiệu chuẩn. Dấu màu/ArUco chạy được trước khi huấn luyện YOLO.",
                "video": "Tệp video có thể chứa mô phỏng hoặc cảnh thực. Nguồn video không tự chứng minh một phép đo đã được kiểm chứng.",
            }[mode]
        )

        self._refresh_summary()

    def set_locked(self, locked):
        self.locked = locked
        self.apply_availability()

    def preview_geometry(self):
        path = Path(self.geom_path.text().strip())
        example = path.name == "geometry.example.json"
        self.geometry_badge.setText(
            "CẤU HÌNH MẪU" if example else "TỆP HÌNH HỌC ĐÃ CHỌN"
        )
        set_tone(self.geometry_badge, "warning" if example else "data")
        try:
            geometry = Geometry.from_json(path)
            self.geometry_summary.setText(
                f"r = {geometry.radius_px:g} px · l = {geometry.rod_px:g} px · "
                f"e = {geometry.slider_offset_px:g} px\nKiểm tra được cấu trúc hình học, chưa xác minh hiệu chuẩn vật lý."
            )
        except (OSError, ValueError, TypeError):
            self.geometry_summary.setText(
                "Chưa đọc được cấu hình hình học hợp lệ. Hãy chọn JSON đã hiệu chuẩn cho cơ cấu."
            )
