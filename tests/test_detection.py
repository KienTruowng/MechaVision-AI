from pathlib import Path
import cv2
import numpy as np
from mechavision.detection import ColorMarkerDetector,create_aruco_sheet,ArucoDetector


def test_color_marker_detector():
    img=np.full((450,600,3),20,dtype=np.uint8)
    for pt,col in [((110,140),(0,0,255)),((285,200),(0,255,0)),((430,325),(255,0,0))]:
        cv2.circle(img,pt,14,col,-1)
    points=ColorMarkerDetector().detect(img,1).landmarks
    assert set(points)=={'pivot','crank','piston'}
    assert abs(points['crank'].x-285)<2


def test_aruco_sheet_and_detection(tmp_path):
    sheet=create_aruco_sheet(str(tmp_path/'markers.png'),marker_size=140)
    assert sheet.exists()
    im=cv2.imread(str(sheet))
    points=ArucoDetector().detect(im,1).landmarks
    assert set(points)=={'pivot','crank','piston'}
