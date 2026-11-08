"""Bảng điều khiển kỹ thuật PySide6. Cài nhóm phụ thuộc `gui` để chạy.

Nguồn mô phỏng luôn được ghi rõ. Camera/video cần tệp JSON hình học đã hiệu chuẩn.
Không kèm trọng số mô hình. Có thể dùng ngay dấu ArUco/màu hoặc dùng YOLO Pose
khi đã có trọng số huấn luyện riêng.
"""
from __future__ import annotations
from collections import deque
from datetime import datetime
from pathlib import Path
import math
import time
import csv
import itertools
import cv2
import numpy as np
from PySide6.QtCore import Qt,QThread,Signal,QTimer,QTranslator,QLocale
from PySide6.QtGui import QImage,QPixmap,QFont,QFontDatabase
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QGridLayout,QLabel,QPushButton,QComboBox,QLineEdit,QFileDialog,QFrame,QMessageBox,
    QStackedWidget,QFormLayout,QDoubleSpinBox,QSpinBox,QTextEdit,QScrollArea,QSizePolicy)
import pyqtgraph as pg
from pyqtgraph.GraphicsScene import exportDialog
from pyqtgraph.exporters import CSVExporter
from .geometry import Geometry
from .synthetic import Simulator,SimConfig,draw_mechanism
from .acquisition import FrameSource
from .processing import Processor
from .detection import make_detector,draw_observations
from .render import twin_frame,decorate_video
from .i18n import status_text, _font

STYLE='''
QWidget { background-color:#0c1524; color:#e9f0fa; font-family:"Segoe UI"; font-size:12px; }
QMainWindow { background-color:#0c1524; }
QFrame#card { background-color:#142239; border:1px solid #263851; border-radius:12px; }
QLabel#heading { font-size:20px; font-weight:700; color:#f1f6ff; }
QLabel#section { font-size:13px; font-weight:700; color:#d8e8fb; }
QLabel#value { font-size:24px; font-weight:700; color:#f5f9ff; }
QLabel#muted { color:#90a4bf; }
QPushButton { background:#243753; padding:9px 14px; border:1px solid #3b5374; border-radius:7px; font-weight:600; }
QPushButton:hover { background:#34537b; }
QPushButton#primary { background:#267ec8; border-color:#318ed7; }
QPushButton#primary:hover { background:#3799e7; }
QPushButton#danger { background:#512b38; border-color:#744157; }
QComboBox,QLineEdit,QDoubleSpinBox,QSpinBox,QTextEdit { background:#0c172a; border:1px solid #344762; padding:6px; border-radius:6px; }
QComboBox QAbstractItemView { background:#142239; color:#e9f0fa; }
'''


class _VietnameseQtTranslator(QTranslator):
    """Các nhãn Qt chuẩn xuất hiện trong hộp chọn tệp và menu nhập văn bản."""
    labels={
        '&Delete':'&Xóa','&Look in:':'&Thư mục:','&New Folder':'Thư mục &mới',
        '&Open':'&Mở','&Rename':'Đổi &tên','All Files (*)':'Tất cả tệp (*)',
        'Back':'Quay lại','Forward':'Tiến tới','Go back':'Quay lại',
        'Go forward':'Tiến tới','Parent Directory':'Thư mục cha',
        'Go to the parent directory':'Về thư mục cha','Create New Folder':'Tạo thư mục mới',
        'Create a New Folder':'Tạo thư mục mới','Detail View':'Xem chi tiết',
        'List View':'Xem danh sách','Change to detail view mode':'Chuyển sang chế độ chi tiết',
        'Change to list view mode':'Chuyển sang chế độ danh sách','File &name:':'Tên &tệp:',
        'Files':'Tệp','Files of &type:':'&Loại tệp:','Show ':'Hiển thị ',
        'Show &hidden files':'Hiện tệp ẩ&n','Sidebar':'Thanh bên',
        'List of places and bookmarks':'Danh sách vị trí và dấu trang',
        'Date Modified':'Ngày sửa đổi','My Computer':'Máy tính','Computer':'Máy tính',
        'Name':'Tên','Size':'Kích thước','Type':'Loại','File':'Tệp','Folder':'Thư mục',
        'Directory':'Thư mục','%1 File':'Tệp %1','File Folder':'Thư mục tệp',
        'Cancel':'Hủy','OK':'Đóng','Open':'Mở','Close':'Đóng','Save':'Lưu',
        '&Undo':'&Hoàn tác','&Redo':'&Làm lại','Cu&t':'Cắ&t','&Copy':'&Sao chép',
        '&Paste':'&Dán','Delete':'Xóa','Select All':'Chọn tất cả','Select &All':'Chọn tất cả',
        'Undo':'Hoàn tác','Redo':'Làm lại','Cut':'Cắt','Copy':'Sao chép','Paste':'Dán',
        'New Folder':'Thư mục mới','File not found':'Không tìm thấy tệp',
        '%1\nFile not found.\nPlease verify the correct file name was given.':'%1\nKhông tìm thấy tệp.\nHãy kiểm tra lại tên tệp.',
        'Directory not found':'Không tìm thấy thư mục',
        '%1\nDirectory not found.\nPlease verify the correct directory name was given.':'%1\nKhông tìm thấy thư mục.\nHãy kiểm tra lại tên thư mục.',
        'ViewBox options':'Tùy chọn vùng xem','View All':'Xem toàn bộ','axis':'trục',
        'Mouse Mode':'Chế độ chuột','3 button':'Ba nút','1 button':'Một nút',
        'Plot Options':'Tùy chọn biểu đồ','Transforms':'Biến đổi','Downsample':'Giảm mẫu',
        'Average':'Trung bình','Alpha':'Độ trong suốt','Grid':'Lưới','Points':'Điểm',
        'Clip to View':'Giới hạn theo vùng xem','Max Traces:':'Số đường tối đa:',
        'Peak':'Đỉnh','Forget hidden traces':'Xóa đường đã ẩn khỏi bộ nhớ',
        'Mean':'Trung bình','Subsample':'Lấy mẫu thưa','Auto':'Tự động',
        'Log X':'Logarit X','Log Y':'Logarit Y','Y vs. Y\'':'Y theo đạo hàm Y',
        'Power Spectrum (FFT)':'Phổ công suất (FFT)','Subtract Mean':'Trừ trung bình',
        'Show X Grid':'Hiện lưới X','Show Y Grid':'Hiện lưới Y','Opacity':'Độ đục',
        'Link Axis:':'Liên kết trục:','Manual':'Thủ công','Invert Axis':'Đảo trục',
        'Mouse Enabled':'Cho phép chuột','Visible Data Only':'Chỉ dữ liệu nhìn thấy',
        'Auto Pan Only':'Chỉ tự động dịch chuyển','Export...':'Xuất…','Export':'Xuất',
        'Item to export:':'Đối tượng cần xuất:','Export format':'Định dạng xuất',
        'Export options':'Tùy chọn xuất','Entire Scene':'Toàn bộ vùng đồ thị',
        'Image File (PNG, TIF, JPG, ...)':'Tệp ảnh (PNG, TIF, JPG, …)',
        'Scalable Vector Graphics (SVG)':'Đồ họa vector SVG','CSV from plot data':'CSV từ dữ liệu biểu đồ',
        'Matplotlib Window':'Cửa sổ Matplotlib','HDF5 Export: plot (x,y)':'Xuất HDF5: biểu đồ (x,y)',
        'CSV of original plot data':'CSV từ dữ liệu biểu đồ gốc',
        'Scalable Vector Graphics':'Đồ họa vector SVG',
        'width':'Chiều rộng','height':'Chiều cao','antialias':'Khử răng cưa',
        'background':'Nền','invertValue':'Đảo độ sáng','scaling stroke':'Co giãn nét',
        'separator':'Dấu phân cách','precision':'Độ chính xác','columnMode':'Bố trí cột',
        'params':'Tham số','Plot':'Biểu đồ','ViewBox':'Vùng xem',
        'comma':'Dấu phẩy','tab':'Dấu tab','(x,y) per plot':'(x,y) cho từng đường',
        '(x,y,y,y) for all plots':'(x,y,y,y) cho tất cả đường',
        'Display averages of the curves displayed in this plot. The parameter list allows you to choose parameters to average over (if any are available).':'Hiển thị trung bình các đường trong biểu đồ. Chọn các tham số cần lấy trung bình nếu có.',
        'Plot only the portion of each curve that is visible. This assumes X values are uniformly spaced.':'Chỉ vẽ phần đường đang nhìn thấy; giả định các giá trị X cách đều.',
        'If multiple curves are displayed in this plot, check this box to limit the number of traces that are displayed.':'Giới hạn số đường hiển thị khi biểu đồ có nhiều đường.',
        'Downsample by drawing a saw wave that follows the min and max of the original data. This method produces the best visual representation of the data but is slower.':'Giảm mẫu theo cực tiểu và cực đại dữ liệu gốc; thể hiện rõ biến thiên nhưng chậm hơn.',
        'If multiple curves are displayed in this plot, check "Max Traces" and set this value to limit the number of traces that are displayed.':'Bật giới hạn số đường rồi đặt số đường tối đa được hiển thị.',
        'If MaxTraces is checked, remove curves from memory after they are hidden (saves memory, but traces can not be un-hidden).':'Khi giới hạn số đường, xóa đường đã ẩn khỏi bộ nhớ; không thể hiện lại đường đã xóa.',
        'Downsample by taking the mean of N samples.':'Giảm mẫu bằng trung bình của N mẫu.',
        'Downsample by taking the first of N samples. This method is fastest and least accurate.':'Giảm mẫu bằng mẫu đầu tiên trong N mẫu; nhanh nhất nhưng kém chính xác nhất.',
        'Automatically downsample data based on the visible range. This assumes X values are uniformly spaced.':'Tự động giảm mẫu theo vùng nhìn thấy; giả định các giá trị X cách đều.',
        'Downsample data before plotting. (plot every Nth sample)':'Giảm mẫu trước khi vẽ, lấy mỗi mẫu thứ N.',
        '<html><head/><body><p>Links this axis with another view. When linked, both views will display the same data range.</p></body></html>':'Liên kết trục với vùng xem khác để dùng chung khoảng dữ liệu.',
        '<html><head/><body><p>Percent of data to be visible when auto-scaling. It may be useful to decrease this value for data with spiky noise.</p></body></html>':'Tỷ lệ dữ liệu nhìn thấy khi tự co giãn; có thể giảm khi dữ liệu có nhiễu xung.',
        '<html><head/><body><p>Automatically resize this axis whenever the displayed data is changed.</p></body></html>':'Tự co giãn trục khi dữ liệu thay đổi.',
        '<html><head/><body><p>Set the range for this axis manually. This disables automatic scaling. </p></body></html>':'Đặt khoảng trục thủ công và tắt tự co giãn.',
        '<html><head/><body><p>Minimum value to display for this axis.</p></body></html>':'Giá trị nhỏ nhất của trục.',
        '<html><head/><body><p>Maximum value to display for this axis.</p></body></html>':'Giá trị lớn nhất của trục.',
        '<html><head/><body><p>Inverts the display of this axis. (+y points downward instead of upward)</p></body></html>':'Đảo chiều hiển thị trục (chiều dương y hướng xuống).',
        '<html><head/><body><p>Enables mouse interaction (panning, scaling) for this axis.</p></body></html>':'Cho phép dịch chuyển và co giãn trục bằng chuột.',
        '<html><head/><body><p>When checked, the axis will only auto-scale to data that is visible along the orthogonal axis.</p></body></html>':'Chỉ tự co giãn theo dữ liệu đang nhìn thấy trên trục vuông góc.',
        '<html><head/><body><p>When checked, the axis will automatically pan to center on the current data, but the scale along this axis will not change.</p></body></html>':'Tự dịch chuyển để căn giữa dữ liệu hiện tại và giữ nguyên tỷ lệ trục.',
    }

    def translate(self,context,sourceText,disambiguation=None,n=-1):
        return self.labels.get(sourceText,'')


class _Utf8CSVExporter(CSVExporter):
    """Xuất các đường của dashboard bằng UTF-8, tránh lỗi bảng mã Windows."""
    def export(self,fileName=None):
        if not isinstance(self.item,pg.PlotItem):
            raise ValueError('Hãy chọn một biểu đồ để xuất CSV.')
        if fileName is None:
            self.fileSaveDialog(filter=['*.csv','*.tsv'])
            return
        headers=[];columns=[]
        for item in self.item.items:
            if not hasattr(item,'implements') or not item.implements('plotData'):continue
            x,y=item.getOriginalDataset() if hasattr(item,'getOriginalDataset') else item.getData()
            if x is None:continue
            name=item.name() or f'Đường {len(headers)}'
            if self.params['columnMode']=='(x,y) per plot' or not columns:
                headers.append(name+'_x');columns.append(x)
            headers.append(name+'_y');columns.append(y)
        separator=',' if self.params['separator']=='comma' else '\t'
        with open(fileName,'w',newline='',encoding='utf-8') as stream:
            writer=csv.writer(stream,delimiter=separator)
            writer.writerow(headers)
            for row in itertools.zip_longest(*columns,fillvalue=''):
                writer.writerow([value if isinstance(value,str) else
                    np.format_float_positional(value,precision=self.params['precision']) for value in row])


class _VietnameseExportDialog(exportDialog.ExportDialog):
    """Dịch nhãn cây và tham số xuất, giữ nguyên tên/giá trị của bộ xuất dữ liệu."""
    def updateItemList(self,*args,**kwargs):
        super().updateItemList(*args,**kwargs)
        def visit(item):
            item.setText(0,_VietnameseQtTranslator.labels.get(item.text(0),item.text(0)))
            for index in range(item.childCount()):visit(item.child(index))
        for index in range(self.ui.itemTree.topLevelItemCount()):
            visit(self.ui.itemTree.topLevelItem(index))

    def exportFormatChanged(self,*args,**kwargs):
        super().exportFormatChanged(*args,**kwargs)
        if self.currentExporter is None:return
        if isinstance(self.currentExporter,CSVExporter):
            self.currentExporter=_Utf8CSVExporter(self.currentExporter.item)
        params=self.currentExporter.parameters()
        if params is None:return
        for param in [params,*params.children()]:
            param.setOpts(title=_VietnameseQtTranslator.labels.get(param.name(),param.name()))
            limits=param.opts.get('limits')
            if param.type()=='list' and isinstance(limits,list) and all(isinstance(v,str) for v in limits):
                param.setLimits({_VietnameseQtTranslator.labels.get(v,v):v for v in limits})
        self.ui.paramTree.setParameters(params)

    def show(self,*args,**kwargs):
        super().show(*args,**kwargs)
        self.resize(640,520)

class Worker(QThread):
    sample=Signal(object,object,object)
    failed=Signal(str)
    ended=Signal()
    def __init__(self,mode,source,detector,weights,geometry_path,log_path,device):
        super().__init__()
        self.mode=mode;self.source=source;self.detector_name=detector
        self.weights=weights;self.geometry_path=geometry_path
        self.log_path=log_path;self.device=device
        self._stop=False

    def stop(self):self._stop=True

    def run(self):
        processor=None
        try:
            geo=Geometry() if self.mode=='simulation' else Geometry.from_json(self.geometry_path)
            processor=Processor(geo,self.log_path)
            if self.mode=='simulation':
                simulator=Simulator(geo,SimConfig(seed=42))
                while not self._stop:
                    t0=time.perf_counter()
                    obs=simulator.step(1/30)
                    metrics=processor.step(obs)
                    frame=draw_mechanism(geo,obs.truth_theta,900,520,obs)
                    est=metrics['physics']
                    twin=twin_frame(geo,est)
                    decorate_video(frame,est.status,metrics['fps'])
                    self.sample.emit(frame,twin,{'observation':obs,'metrics':metrics,'synthetic':True})
                    self.msleep(max(1,int(1000/30-(time.perf_counter()-t0)*1000)))
            else:
                detector=make_detector(self.detector_name,self.weights,self.device)
                src=int(self.source) if self.mode=='camera' else self.source
                with FrameSource(src) as capture:
                    while not self._stop:
                        sample=capture.read()
                        if sample is None:break
                        frame,ts,index=sample
                        obs=detector.detect(frame,ts,index)
                        metrics=processor.step(obs)
                        est=metrics['physics']
                        overlay=draw_observations(frame.copy(),obs)
                        decorate_video(overlay,est.status,metrics['fps'])
                        twin=twin_frame(geo,est)
                        self.sample.emit(overlay,twin,{'observation':obs,'metrics':metrics,'synthetic':False})
                        if self.mode=='video':self.msleep(20)
        except Exception as e:
            self.failed.emit(f'{type(e).__name__}: {e}')
        finally:
            if processor:processor.close()
            self.ended.emit()


def _card():
    w=QFrame();w.setObjectName('card');return w


def _image_label():
    label=QLabel('Đang chờ nguồn dữ liệu…');label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet('background:#0b1422; border-radius:8px; color:#8195ad;')
    label.setMinimumSize(200,150)
    label.setScaledContents(False)
    label.setSizePolicy(QSizePolicy.Ignored,QSizePolicy.Ignored)
    return label


def _message(parent,title,text,icon=QMessageBox.Warning):
    box=QMessageBox(icon,title,text,QMessageBox.Ok,parent)
    box.button(QMessageBox.Ok).setText('Đóng')
    box.exec()


class _DashboardScrollArea(QScrollArea):
    """Co bố cục theo cửa sổ; chỉ cuộn khi nhỏ hơn kích thước tối thiểu."""
    def resizeEvent(self,event):
        super().resizeEvent(event)
        content=self.widget()
        if content:
            content.resize(max(1120,self.viewport().width()),
                           max(content.minimumSizeHint().height(),self.viewport().height()))

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Nạp phông trực tiếp để cả Qt offscreen và máy thiếu bộ nhớ đệm phông đều đọc được dấu.
        font_id=QFontDatabase.addApplicationFont(str(_font(12).path))
        if font_id>=0:
            family=QFontDatabase.applicationFontFamilies(font_id)[0]
            QApplication.instance().setFont(QFont(family,10))
        app=QApplication.instance()
        if not hasattr(app,'_mechavision_translator'):
            app._mechavision_translator=_VietnameseQtTranslator(app)
            app.installTranslator(app._mechavision_translator)
        QLocale.setDefault(QLocale('vi_VN'))
        self.setWindowTitle('MechaVision AI — Ước lượng thị giác có ràng buộc vật lý')
        self.resize(1450,900)
        self.setStyleSheet(STYLE)
        self.worker=None
        self.timestamps=deque(maxlen=400)
        self.angles_raw=deque(maxlen=400)
        self.angles_est=deque(maxlen=400)
        self.piston_meas=deque(maxlen=400)
        self.piston_pred=deque(maxlen=400)
        self.fps_series=deque(maxlen=400)
        self._img_main=None;self._img_twin=None
        self._build()

    def _build(self):
        container=QWidget();container.setMinimumWidth(1120)
        container.setSizePolicy(QSizePolicy.Expanding,QSizePolicy.Ignored)
        scroll=_DashboardScrollArea();scroll.setWidget(container)
        self.setCentralWidget(scroll)
        layout=QVBoxLayout(container);layout.setContentsMargins(18,16,18,14);layout.setSpacing(12)
        header=QHBoxLayout()
        logo=QLabel('MECHAVISION  /  AI');logo.setObjectName('heading');header.addWidget(logo)
        sub=QLabel('Ước lượng trạng thái bằng thị giác • Công cụ nghiên cứu');sub.setObjectName('muted');header.addWidget(sub)
        header.addStretch()
        layout.addLayout(header)
        header=QHBoxLayout()
        self.source_mode=QComboBox()
        for label,value in [('Mô phỏng','simulation'),('Camera trực tiếp','camera'),('Video đã ghi','video')]:self.source_mode.addItem(label,value)
        header.addWidget(QLabel('Nguồn'));header.addWidget(self.source_mode)
        self.detector_mode=QComboBox()
        for label,value in [('Dấu màu','color'),('Dấu ArUco','aruco'),('YOLO Pose','yolo')]:self.detector_mode.addItem(label,value)
        header.addWidget(QLabel('Nhận diện'));header.addWidget(self.detector_mode)
        header.addStretch()
        self.start_btn=QPushButton('Bắt đầu phân tích');self.start_btn.setObjectName('primary');self.start_btn.clicked.connect(self.start);header.addWidget(self.start_btn)
        self.stop_btn=QPushButton('Dừng');self.stop_btn.setObjectName('danger');self.stop_btn.setEnabled(False);self.stop_btn.clicked.connect(self.stop);header.addWidget(self.stop_btn)
        layout.addLayout(header)
        inputs=QGridLayout();inputs.setColumnStretch(1,1);inputs.setColumnStretch(4,1)
        self.input_source=QLineEdit('0');self.input_source.setPlaceholderText('Số hiệu camera (0) hoặc đường dẫn video')
        inputs.addWidget(QLabel('Camera / video'),0,0);inputs.addWidget(self.input_source,0,1)
        source_select=QPushButton('Chọn video');source_select.clicked.connect(lambda:self._browse(self.input_source,'Video (*.mp4 *.avi *.mov *.mkv);;Tất cả tệp (*)'));inputs.addWidget(source_select,0,2)
        self.geom_path=QLineEdit('configs/geometry.example.json');inputs.addWidget(QLabel('Hình học JSON'),0,3);inputs.addWidget(self.geom_path,0,4)
        self.geom_path.setToolTip('Camera/video cần tệp hiệu chuẩn của cơ cấu thực. Tệp geometry.example.json chỉ là ví dụ.')
        geom_select=QPushButton('Chọn tệp');geom_select.clicked.connect(lambda:self._browse(self.geom_path,'Tệp JSON (*.json)'));inputs.addWidget(geom_select,0,5)
        self.weights_path=QLineEdit();self.weights_path.setPlaceholderText('YOLO Pose đã huấn luyện (.pt); không cần khi dùng dấu chuẩn');inputs.addWidget(QLabel('Trọng số'),1,0);inputs.addWidget(self.weights_path,1,1,1,4)
        weights_btn=QPushButton('Chọn tệp');weights_btn.clicked.connect(lambda:self._browse(self.weights_path,'Trọng số PyTorch (*.pt)'));inputs.addWidget(weights_btn,1,5)
        layout.addLayout(inputs)
        self.banner=QLabel('SẴN SÀNG — Mô phỏng dùng dữ liệu tổng hợp; phép đo camera/video cần hiệu chuẩn.');self.banner.setObjectName('muted');layout.addWidget(self.banner)
        self.banner.setWordWrap(True)
        self.confidence_label=QLabel('Chưa có ước lượng để đánh giá độ tin cậy.');self.confidence_label.setWordWrap(True);layout.addWidget(self.confidence_label)
        split=QHBoxLayout();split.setSpacing(12)
        for title,attr in [('CAMERA / QUAN SÁT','camera_label'),('MÔ HÌNH SỐ / TRẠNG THÁI ƯỚC LƯỢNG','twin_label')]:
            card=_card();v=QVBoxLayout(card);t=QLabel(title);t.setObjectName('section');v.addWidget(t)
            label=_image_label();setattr(self,attr,label);v.addWidget(label,1)
            split.addWidget(card,1)
        layout.addLayout(split,5)
        stats=QHBoxLayout()
        for title,attribute in [('TRẠNG THÁI','state_label'),('GÓC (°)','angle_label'),('TỐC ĐỘ (vòng/phút)','rpm_label'),('ĐỘ BẤT ĐỊNH (°)','sigma_label'),('SAI LỆCH (px)','resid_label'),('XỬ LÝ (khung/giây)','fps_label')]:
            card=_card();v=QVBoxLayout(card)
            small=QLabel(title);small.setObjectName('muted');small.setWordWrap(True);v.addWidget(small)
            big=QLabel('—');big.setObjectName('value');big.setWordWrap(True);setattr(self,attribute,big);v.addWidget(big)
            stats.addWidget(card,1)
        self.state_label.setStyleSheet('font-size:18px;')
        self.sigma_label.setToolTip('Độ lệch chuẩn của góc do EKF ước lượng; chưa được hiệu chuẩn bằng dữ liệu thực.')
        self.resid_label.setToolTip('Chênh lệch vị trí pít-tông quan sát và vị trí từ góc chốt khuỷu theo mô hình; không phải kết luận hư hỏng.')
        layout.addLayout(stats)
        graphs=QHBoxLayout();graphs.setSpacing(12)
        pg.setConfigOption('background','#142239');pg.setConfigOption('foreground','#a9bbcf')
        angle_card=_card();vv=QVBoxLayout(angle_card);vv.addWidget(QLabel('GÓC | ĐO TRỰC TIẾP VÀ EKF VẬT LÝ'))
        self.angle_plot=pg.PlotWidget();self.angle_plot.showGrid(x=True,y=True,alpha=.17)
        self.angle_plot.addLegend(offset=(-12,8));self.angle_plot.setLabel('left','Góc','°');self.angle_plot.setLabel('bottom','Thời gian','s')
        self.angle_raw_curve=self.angle_plot.plot(pen=pg.mkPen('#e0a458',width=1.7),name='Góc từ điểm đặc trưng')
        self.angle_ekf_curve=self.angle_plot.plot(pen=pg.mkPen('#6aaef6',width=2.2),name='EKF vật lý')
        vv.addWidget(self.angle_plot);graphs.addWidget(angle_card,1)
        piston_card=_card();vp=QVBoxLayout(piston_card);vp.addWidget(QLabel('VỊ TRÍ PÍT-TÔNG | QUAN SÁT VÀ ƯỚC LƯỢNG'))
        self.piston_plot=pg.PlotWidget();self.piston_plot.showGrid(x=True,y=True,alpha=.17)
        self.piston_plot.addLegend(offset=(-12,8));self.piston_plot.setLabel('left','Vị trí','px');self.piston_plot.setLabel('bottom','Thời gian','s')
        self.piston_obs_curve=self.piston_plot.plot(pen=pg.mkPen('#e0a458',width=1.7),name='Quan sát')
        self.piston_est_curve=self.piston_plot.plot(pen=pg.mkPen('#62d6b2',width=2.2),name='Ước lượng động học')
        for plot in (self.angle_plot,self.piston_plot):
            dialog=_VietnameseExportDialog(plot.scene());dialog.setParent(self,Qt.Window)
            plot.scene().exportDialog=dialog
        vp.addWidget(self.piston_plot);graphs.addWidget(piston_card,1)
        layout.addLayout(graphs,3)
        footer=QHBoxLayout();self.session_text=QLabel('Chưa có phiên đang chạy');self.session_text.setObjectName('muted');self.session_text.setWordWrap(True);footer.addWidget(self.session_text,1)
        footer.addStretch();notice=QLabel('Ước lượng nghiên cứu ≠ chẩn đoán hư hỏng cơ khí');notice.setObjectName('muted');footer.addWidget(notice)
        layout.addLayout(footer)

    def _browse(self,widget,filter):
        dialog=QFileDialog(self,'Chọn tệp')
        dialog.setOption(QFileDialog.DontUseNativeDialog)
        dialog.setFileMode(QFileDialog.ExistingFile);dialog.setNameFilter(filter)
        for role,text in [(QFileDialog.LookIn,'Thư mục:'),(QFileDialog.FileName,'Tên tệp:'),(QFileDialog.FileType,'Loại tệp:'),(QFileDialog.Accept,'Mở'),(QFileDialog.Reject,'Hủy')]:dialog.setLabelText(role,text)
        dialog.setToolTip('Chọn tệp phù hợp rồi nhấn Mở.')
        if dialog.exec():widget.setText(dialog.selectedFiles()[0])

    def start(self):
        if self.worker and self.worker.isRunning():return
        mode=self.source_mode.currentData();geometry=self.geom_path.text().strip()
        if mode!='simulation' and not Path(geometry).is_file():
            _message(self,'Cần hiệu chuẩn','Phép đo camera/video cần tệp JSON hình học đã hiệu chuẩn. Hãy chạy lệnh calibrate trước.')
            return
        if mode!='simulation' and self.detector_mode.currentData()=='yolo' and not Path(self.weights_path.text()).is_file():
            _message(self,'Cần trọng số YOLO','Hãy huấn luyện mô hình ba điểm đặc trưng rồi chọn best.pt, hoặc dùng dấu màu/ArUco.')
            return
        source=self.input_source.text().strip()
        if mode=='camera' and not source.isdigit():
            _message(self,'Camera','Nguồn camera phải là số nguyên (0, 1, …)');return
        if mode=='video' and not Path(source).is_file():
            _message(self,'Video','Hãy chọn một tệp video hiện có.');return
        for buf in (self.timestamps,self.angles_raw,self.angles_est,self.piston_meas,self.piston_pred,self.fps_series):buf.clear()
        filename=f'outputs/session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        self.worker=Worker(mode,source,self.detector_mode.currentData(),
                           self.weights_path.text().strip() or None,geometry,filename,'cpu')
        self.worker.sample.connect(self._on_sample)
        self.worker.failed.connect(self._on_error)
        self.worker.ended.connect(self._on_end)
        self.worker.start()
        self.start_btn.setEnabled(False);self.stop_btn.setEnabled(True)
        self.session_text.setText(f'Nhật ký CSV → {filename}')
        self.banner.setText({'simulation':'DỮ LIỆU MÔ PHỎNG — KHÔNG PHẢI PHÉP ĐO ĐỘNG CƠ THỰC','camera':'ĐO CAMERA TRỰC TIẾP — PHỤ THUỘC HIỆU CHUẨN','video':'PHÂN TÍCH VIDEO ĐÃ GHI — PHỤ THUỘC HIỆU CHUẨN; CẦN XÁC MINH NGUỒN VIDEO'}[mode])
        for widget in (self.source_mode,self.detector_mode,self.input_source,self.geom_path,self.weights_path):widget.setEnabled(False)

    def stop(self):
        if self.worker:self.worker.stop()
        self.stop_btn.setEnabled(False)

    def _on_error(self,message):
        self.banner.setText('LỖI: '+message)
        _message(self,'Lỗi MechaVision','Không thể hoàn tất phiên xử lý.\n'+message)

    def _on_end(self):
        self.start_btn.setEnabled(True);self.stop_btn.setEnabled(False)
        for widget in (self.source_mode,self.detector_mode,self.input_source,self.geom_path,self.weights_path):widget.setEnabled(True)
        self.session_text.setText(self.session_text.text()+' — Đã kết thúc phiên')
        self.confidence_label.setText('Phiên đã dừng. Các giá trị đang hiển thị là mẫu cuối cùng, không phải phép đo đang chạy.')

    def _render_image(self,label,frame):
        h,w,ch=frame.shape
        image=QImage(frame.data,w,h,frame.strides[0],QImage.Format_BGR888).copy()
        pix=QPixmap.fromImage(image)
        label.setPixmap(pix.scaled(label.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        # Vẽ lại khung hình khi có mẫu mới.

    def _on_sample(self,frame,twin,data):
        self._render_image(self.camera_label,frame)
        self._render_image(self.twin_label,twin)
        obs=data['observation'];metrics=data['metrics'];est=metrics['physics']
        self.state_label.setText(status_text(est.status))
        self.state_label.setStyleSheet('font-size:18px; color:'+{'TRACKING':'#67d5a3','PREDICTED':'#f4c27b','LOST':'#ef8a91'}.get(est.status,'#90a4bf'))
        self.confidence_label.setText({'TRACKING':'Đang cập nhật từ quan sát được chấp nhận; độ bất định là ước lượng của bộ lọc.',
            'PREDICTED':'Đang dự báo ngắn hạn theo mô hình; chưa có quan sát mới được chấp nhận.',
            'LOST':'KHÔNG ĐỦ ĐỘ TIN CẬY — Đã mất dấu hoặc vượt giới hạn bất định; tạm ngừng hiển thị góc và tốc độ.',
            'UNINITIALIZED':'CHƯA KHỞI TẠO — Cần quan sát chốt khuỷu để bắt đầu ước lượng.'}.get(est.status,'Không xác định được độ tin cậy.'))
        self.angle_label.setText('—' if est.theta is None else f'{math.degrees(est.theta):.1f}')
        self.rpm_label.setText('—' if est.rpm is None else f'{est.rpm:.1f}')
        self.sigma_label.setText('—' if est.sigma_theta is None else f'{math.degrees(est.sigma_theta):.1f}')
        self.resid_label.setText('—' if est.kinematic_discrepancy_px is None else f'{est.kinematic_discrepancy_px:.1f}')
        self.fps_label.setText(f'{metrics["fps"]:.1f}')
        self.timestamps.append(obs.timestamp)
        self.angles_raw.append(math.degrees(metrics['measured_theta']) if metrics['measured_theta'] is not None else float('nan'))
        self.angles_est.append(math.degrees(est.theta) if est.theta is not None else float('nan'))
        self.piston_meas.append(metrics['observed_x'] if metrics['observed_x'] is not None else float('nan'))
        self.piston_pred.append(metrics['predicted_x'] if metrics['predicted_x'] is not None else float('nan'))
        if len(self.timestamps)%3==0:
            t=list(self.timestamps)
            self.angle_raw_curve.setData(t,list(self.angles_raw))
            self.angle_ekf_curve.setData(t,list(self.angles_est))
            self.piston_obs_curve.setData(t,list(self.piston_meas))
            self.piston_est_curve.setData(t,list(self.piston_pred))

    def closeEvent(self,event):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            if not self.worker.wait(3500):
                event.ignore();_message(self,'Đang dừng','Luồng xử lý đang dừng. Vui lòng thử đóng lại sau.',QMessageBox.Information);return
        event.accept()


def launch():
    import sys
    app=QApplication.instance() or QApplication(sys.argv)
    w=MainWindow();w.show()
    sys.exit(app.exec())
