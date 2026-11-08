"""PySide6 engineering dashboard. Install optional `gui` extra to run.

The SIMULATION source is explicitly flagged; it never impersonates a live feed.
Live camera/video requires a calibrated geometry JSON file. No model weights
are bundled. Camera sources can use ArUco/color markers immediately or a
trained YOLO pose model when such weights exist.
"""
from __future__ import annotations
from collections import deque
from datetime import datetime
from pathlib import Path
import math
import time
import cv2
import numpy as np
from PySide6.QtCore import Qt,QThread,Signal,QTimer
from PySide6.QtGui import QImage,QPixmap,QFont
from PySide6.QtWidgets import (QApplication,QMainWindow,QWidget,QVBoxLayout,QHBoxLayout,
    QGridLayout,QLabel,QPushButton,QComboBox,QLineEdit,QFileDialog,QFrame,QMessageBox,
    QStackedWidget,QFormLayout,QDoubleSpinBox,QSpinBox,QTextEdit)
import pyqtgraph as pg
from .geometry import Geometry
from .synthetic import Simulator,SimConfig,draw_mechanism
from .acquisition import FrameSource
from .processing import Processor
from .detection import make_detector,draw_observations
from .render import twin_frame,decorate_video

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
    label=QLabel('Waiting for source...');label.setAlignment(Qt.AlignCenter)
    label.setStyleSheet('background:#0b1422; border-radius:8px; color:#8195ad;')
    label.setMinimumSize(200,150)
    label.setScaledContents(False)
    return label

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('MechaVision AI — Physics-Constrained Visual Estimation')
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
        container=QWidget();self.setCentralWidget(container)
        layout=QVBoxLayout(container);layout.setContentsMargins(18,16,18,14);layout.setSpacing(12)
        header=QHBoxLayout()
        logo=QLabel('MECHAVISION  /  AI');logo.setObjectName('heading');header.addWidget(logo)
        sub=QLabel('Visual State Estimation  •  Research Workbench');sub.setObjectName('muted');header.addWidget(sub)
        header.addStretch()
        self.source_mode=QComboBox();self.source_mode.addItems(['simulation','camera','video']);header.addWidget(QLabel('Source'));header.addWidget(self.source_mode)
        self.detector_mode=QComboBox();self.detector_mode.addItems(['color','aruco','yolo']);header.addWidget(QLabel('Detector'));header.addWidget(self.detector_mode)
        self.start_btn=QPushButton('Start analysis');self.start_btn.setObjectName('primary');self.start_btn.clicked.connect(self.start);header.addWidget(self.start_btn)
        self.stop_btn=QPushButton('Stop');self.stop_btn.setObjectName('danger');self.stop_btn.setEnabled(False);self.stop_btn.clicked.connect(self.stop);header.addWidget(self.stop_btn)
        layout.addLayout(header)
        inputs=QHBoxLayout()
        self.input_source=QLineEdit('0');self.input_source.setPlaceholderText('Camera number (0) or video path');inputs.addWidget(QLabel('Camera / video'));inputs.addWidget(self.input_source,2)
        self.geom_path=QLineEdit('configs/geometry.example.json');inputs.addWidget(QLabel('Geometry JSON'));inputs.addWidget(self.geom_path,2)
        geom_select=QPushButton('Browse');geom_select.clicked.connect(lambda:self._browse(self.geom_path,'JSON files (*.json)'));inputs.addWidget(geom_select)
        self.weights_path=QLineEdit();self.weights_path.setPlaceholderText('Trained YOLO pose .pt (optional for marker mode)');inputs.addWidget(QLabel('Weights'));inputs.addWidget(self.weights_path,2)
        weights_btn=QPushButton('Browse');weights_btn.clicked.connect(lambda:self._browse(self.weights_path,'PyTorch weights (*.pt)'));inputs.addWidget(weights_btn)
        layout.addLayout(inputs)
        self.banner=QLabel('READY — simulation is synthetic; camera/video data requires calibration.');self.banner.setObjectName('muted');layout.addWidget(self.banner)
        split=QHBoxLayout();split.setSpacing(12)
        for title,attr in [('CAMERA / OBSERVATIONS','camera_label'),('DIGITAL TWIN / ESTIMATED STATE','twin_label')]:
            card=_card();v=QVBoxLayout(card);t=QLabel(title);t.setObjectName('section');v.addWidget(t)
            label=_image_label();setattr(self,attr,label);v.addWidget(label,1)
            split.addWidget(card,1)
        layout.addLayout(split,5)
        stats=QHBoxLayout()
        for title,attribute in [('STATE','state_label'),('ANGLE (DEG)','angle_label'),('SPEED (RPM)','rpm_label'),('UNCERTAINTY (DEG)','sigma_label'),('DISCREPANCY (PX)','resid_label'),('PROCESSING (FPS)','fps_label')]:
            card=_card();v=QVBoxLayout(card)
            small=QLabel(title);small.setObjectName('muted');v.addWidget(small)
            big=QLabel('—');big.setObjectName('value');setattr(self,attribute,big);v.addWidget(big)
            stats.addWidget(card)
        layout.addLayout(stats)
        graphs=QHBoxLayout();graphs.setSpacing(12)
        pg.setConfigOption('background','#142239');pg.setConfigOption('foreground','#a9bbcf')
        angle_card=_card();vv=QVBoxLayout(angle_card);vv.addWidget(QLabel('ANGLE  |  RAW vs PHYSICS EKF'))
        self.angle_plot=pg.PlotWidget();self.angle_plot.showGrid(x=True,y=True,alpha=.17)
        self.angle_plot.addLegend(offset=(-12,8));self.angle_plot.setLabel('left','deg');self.angle_plot.setLabel('bottom','time','s')
        self.angle_raw_curve=self.angle_plot.plot(pen=pg.mkPen('#e0a458',width=1.7),name='raw keypoint')
        self.angle_ekf_curve=self.angle_plot.plot(pen=pg.mkPen('#6aaef6',width=2.2),name='physics EKF')
        vv.addWidget(self.angle_plot);graphs.addWidget(angle_card,1)
        piston_card=_card();vp=QVBoxLayout(piston_card);vp.addWidget(QLabel('PISTON POSITION  |  OBSERVED vs ESTIMATED'))
        self.piston_plot=pg.PlotWidget();self.piston_plot.showGrid(x=True,y=True,alpha=.17)
        self.piston_plot.addLegend(offset=(-12,8));self.piston_plot.setLabel('left','pixel');self.piston_plot.setLabel('bottom','time','s')
        self.piston_obs_curve=self.piston_plot.plot(pen=pg.mkPen('#e0a458',width=1.7),name='observed')
        self.piston_est_curve=self.piston_plot.plot(pen=pg.mkPen('#62d6b2',width=2.2),name='kinematic estimate')
        vp.addWidget(self.piston_plot);graphs.addWidget(piston_card,1)
        layout.addLayout(graphs,3)
        footer=QHBoxLayout();self.session_text=QLabel('No active session');self.session_text.setObjectName('muted');footer.addWidget(self.session_text)
        footer.addStretch();notice=QLabel('Scientific estimate ≠ mechanical fault diagnosis');notice.setObjectName('muted');footer.addWidget(notice)
        layout.addLayout(footer)

    def _browse(self,widget,filter):
        file,_=QFileDialog.getOpenFileName(self,'Select file','',filter)
        if file:widget.setText(file)

    def start(self):
        if self.worker and self.worker.isRunning():return
        mode=self.source_mode.currentText();geometry=self.geom_path.text().strip()
        if mode!='simulation' and not Path(geometry).is_file():
            QMessageBox.warning(self,'Calibration needed','Real camera/video requires a calibrated geometry JSON. Run the calibrate command first.')
            return
        if mode!='simulation' and self.detector_mode.currentText()=='yolo' and not Path(self.weights_path.text()).is_file():
            QMessageBox.warning(self,'YOLO weights needed','Train your 3-keypoint model and choose best.pt, or select color/aruco markers.')
            return
        source=self.input_source.text().strip()
        if mode=='camera' and not source.isdigit():
            QMessageBox.warning(self,'Camera','Camera source must be an integer (0, 1, ...)');return
        if mode=='video' and not Path(source).is_file():
            QMessageBox.warning(self,'Video','Select an existing video file.');return
        for buf in (self.timestamps,self.angles_raw,self.angles_est,self.piston_meas,self.piston_pred,self.fps_series):buf.clear()
        filename=f'outputs/session_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        self.worker=Worker(mode,source,self.detector_mode.currentText(),
                           self.weights_path.text().strip() or None,geometry,filename,'cpu')
        self.worker.sample.connect(self._on_sample)
        self.worker.failed.connect(self._on_error)
        self.worker.ended.connect(self._on_end)
        self.worker.start()
        self.start_btn.setEnabled(False);self.stop_btn.setEnabled(True)
        self.session_text.setText(f'CSV log → {filename}')
        self.banner.setText(('SIMULATED DATA — NOT AN ENGINE MEASUREMENT' if mode=='simulation' else 'LIVE OBSERVATION — CALIBRATION-DEPENDENT'))

    def stop(self):
        if self.worker:self.worker.stop()
        self.stop_btn.setEnabled(False)

    def _on_error(self,message):
        self.banner.setText('ERROR: '+message)
        QMessageBox.warning(self,'MechaVision error',message)

    def _on_end(self):
        self.start_btn.setEnabled(True);self.stop_btn.setEnabled(False)

    def _render_image(self,label,frame):
        h,w,ch=frame.shape
        image=QImage(frame.data,w,h,frame.strides[0],QImage.Format_BGR888).copy()
        pix=QPixmap.fromImage(image)
        label.setPixmap(pix.scaled(label.size(),Qt.KeepAspectRatio,Qt.SmoothTransformation))

    def resizeEvent(self,event):
        super().resizeEvent(event)
        # Frames are redrawn on the next new sample.

    def _on_sample(self,frame,twin,data):
        self._render_image(self.camera_label,frame)
        self._render_image(self.twin_label,twin)
        obs=data['observation'];metrics=data['metrics'];est=metrics['physics']
        self.state_label.setText(est.status)
        self.state_label.setStyleSheet('color:'+{'TRACKING':'#67d5a3','PREDICTED':'#f4c27b','LOST':'#ef8a91'}.get(est.status,'#90a4bf'))
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
                event.ignore();QMessageBox.information(self,'Stopping','The worker is still stopping. Please try closing again.');return
        event.accept()


def launch():
    import sys
    app=QApplication.instance() or QApplication(sys.argv)
    w=MainWindow();w.show()
    sys.exit(app.exec())
