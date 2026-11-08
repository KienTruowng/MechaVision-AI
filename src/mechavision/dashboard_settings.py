"""Cấu hình nguồn và mô hình, tách khỏi không gian giám sát."""

from pathlib import Path
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QComboBox,
    QLineEdit,
    QPushButton,
    QFormLayout,
    QScrollArea,
)
from .dashboard_widgets import panel, text_label, badge, set_tone
from .geometry import Geometry


class SettingsPage(QScrollArea):
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
        layout.addWidget(
            text_label(
                "Cấu hình được áp dụng khi bắt đầu phiên mới. Các trường nguồn được khóa trong khi đang thu nhận.",
                "muted",
                True,
            )
        )
        columns = QHBoxLayout()
        columns.setSpacing(12)
        self.source_card, source_layout = panel(
            "NGUỒN DỮ LIỆU",
            "Chọn rõ dữ liệu mô phỏng, camera trực tiếp hoặc tệp video.",
        )
        source_form = QFormLayout()
        source_form.setSpacing(12)
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
        self.detector_mode = QComboBox()
        for title, value in [
            ("Dấu màu", "color"),
            ("Dấu ArUco", "aruco"),
            ("YOLO Pose", "yolo"),
        ]:
            self.detector_mode.addItem(title, value)
        source_form.addRow("Bộ nhận diện", self.detector_mode)
        source_layout.addLayout(source_form)
        self.source_hint = text_label("", "muted", True)
        source_layout.addWidget(self.source_hint)
        source_layout.addStretch()
        columns.addWidget(self.source_card, 1)

        self.model_card, model_layout = panel(
            "HÌNH HỌC VÀ NHẬN DIỆN",
            "Giữ nguyên mô hình tay quay–con trượt và thứ tự ba điểm.",
        )
        model_form = QFormLayout()
        model_form.setSpacing(12)
        model_form.setFieldGrowthPolicy(QFormLayout.AllNonFixedFieldsGrow)
        self.geom_path = QLineEdit("configs/geometry.example.json")
        model_form.addRow("Hình học JSON", self.geom_path)
        self.geometry_button = QPushButton("Chọn cấu hình hình học")
        self.geometry_button.clicked.connect(
            lambda: (browse(self.geom_path, "JSON (*.json)"), self.preview_geometry())
        )
        model_form.addRow("", self.geometry_button)
        self.weights_path = QLineEdit()
        self.weights_path.setPlaceholderText("Trọng số YOLO Pose đã huấn luyện (.pt)")
        model_form.addRow("Trọng số YOLO", self.weights_path)
        self.weights_button = QPushButton("Chọn trọng số")
        self.weights_button.clicked.connect(
            lambda: browse(self.weights_path, "PyTorch (*.pt)")
        )
        model_form.addRow("", self.weights_button)
        self.device = QLineEdit("cpu")
        self.device.setToolTip(
            "Thiết bị YOLO: cpu hoặc chỉ số GPU, ví dụ 0. Không thay đổi tham số bộ lọc."
        )
        model_form.addRow("Thiết bị YOLO", self.device)
        model_layout.addLayout(model_form)
        self.geometry_badge = badge("CẤU HÌNH MẪU", "warning")
        model_layout.addWidget(self.geometry_badge)
        self.geometry_summary = text_label("", "muted", True)
        model_layout.addWidget(self.geometry_summary)
        columns.addWidget(self.model_card, 1)
        layout.addLayout(columns)

        self.logging_card, log_layout = panel(
            "LƯU TRỮ PHIÊN",
            "Nhật ký ghi phép đo và kết quả gốc. Giá trị thiếu được để trống, không thay bằng số không.",
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
                "Mỗi phiên tạo một CSV riêng. Không kèm trọng số riêng cho động cơ và không tự tạo góc tham chiếu thực.",
                "muted",
                True,
            )
        )
        layout.addWidget(self.logging_card)
        notes, notes_layout = panel("TRƯỚC KHI ĐO CƠ CẤU THỰC")
        notes_layout.addWidget(
            text_label(
                "01  Gá camera cố định, gần vuông góc với mặt phẳng chuyển động.\n"
                "02  Chọn đúng tâm quay, chốt khuỷu và khớp thanh truyền–pít-tông.\n"
                "03  Hiệu chuẩn hình học riêng; tệp ví dụ không xác nhận độ chính xác đo thực.",
                "muted",
                True,
            )
        )
        layout.addWidget(notes)
        layout.addStretch()
        self.source_mode.currentIndexChanged.connect(self._source_changed)
        self.detector_mode.currentIndexChanged.connect(self.apply_availability)
        self.geom_path.editingFinished.connect(self.preview_geometry)
        self.apply_availability()
        self.preview_geometry()

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
