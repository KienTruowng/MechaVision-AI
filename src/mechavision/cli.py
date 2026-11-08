"""Công cụ dòng lệnh MechaVision AI: đo trực tiếp, hiệu chuẩn, dữ liệu, huấn luyện và đánh giá."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from .geometry import Geometry
from .synthetic import Simulator,SimConfig
from .estimators import MotionEKF
from .evaluation import run_evaluation
from .session import SessionWriter


class VietnameseArgumentParser(argparse.ArgumentParser):
    """Dịch phần trợ giúp/lỗi của argparse, giữ nguyên lệnh và giá trị lựa chọn."""
    def __init__(self,*args,**kwargs):
        super().__init__(*args,**kwargs)
        self._positionals.title='Đối số vị trí'
        self._optionals.title='Tùy chọn'
        for action in self._actions:
            if isinstance(action,argparse._HelpAction):
                action.help='Hiển thị trợ giúp và thoát'

    def format_help(self):
        return super().format_help().replace('usage: ','Cách dùng: ',1)

    def format_usage(self):
        return super().format_usage().replace('usage: ','Cách dùng: ',1)

    def error(self,message):
        for old,new in [('the following arguments are required','cần các đối số sau'),
                        ('unrecognized arguments','đối số không được hỗ trợ'),
                        ('invalid choice','lựa chọn không hợp lệ'),
                        ('choose from','chọn trong'),
                        ('expected one argument','cần một giá trị'),
                        ('not allowed with argument','không được dùng cùng đối số'),
                        ('invalid int value','giá trị số nguyên không hợp lệ'),
                        ('invalid float value','giá trị số thực không hợp lệ'),
                        ('argument ','đối số ')]:
            message=message.replace(old,new)
        self.print_usage(sys.stderr)
        self.exit(2,f'{self.prog}: lỗi: {message}\n')


def main(argv=None):
    # Bảo đảm tiếng Việt có dấu khi chuyển hướng đầu ra trên Windows.
    for stream in (sys.stdout,sys.stderr):
        if hasattr(stream,'reconfigure'):stream.reconfigure(encoding='utf-8')
    parser=VietnameseArgumentParser(prog='mechavision',description='MechaVision AI — ước lượng trạng thái bằng thị giác có ràng buộc vật lý')
    sub=parser.add_subparsers(dest='command',required=True)
    sim=sub.add_parser('simulate',help='Tạo quan sát mô phỏng và CSV (không phải bằng chứng thực nghiệm)')
    sim.add_argument('--seconds',type=float,default=12)
    sim.add_argument('--fps',type=int,default=30)
    sim.add_argument('--out',default='outputs/synthetic_session.csv')
    sim.add_argument('--seed',type=int,default=42)
    eva=sub.add_parser('evaluate',help='So sánh loại bỏ thành phần trên mô phỏng có thể tái lập')
    eva.add_argument('--seconds',type=float,default=24)
    eva.add_argument('--fps',type=int,default=30)
    eva.add_argument('--seed',type=int,default=42)
    eva.add_argument('--noise',type=float,default=3)
    eva.add_argument('--out',default='outputs/evaluation')
    sub.add_parser('gui',help='Mở bảng điều khiển PySide6 (mô phỏng và camera trực tiếp)')
    markers=sub.add_parser('markers',help='Tạo trang dấu chuẩn ArUco để in')
    markers.add_argument('--out',default='assets/aruco_markers.png')
    cal=sub.add_parser('calibrate',help='Hiệu chuẩn tay quay–con trượt bằng bốn điểm')
    cal.add_argument('--source',default='0',help='Số hiệu camera hoặc đường dẫn video')
    cal.add_argument('--out',default='configs/geometry.json')
    live=sub.add_parser('live',help='Theo dõi phép đo camera/video bằng OpenCV')
    live.add_argument('--source',default='0')
    live.add_argument('--detector',choices=['color','aruco','yolo'],default='color')
    live.add_argument('--weights',default=None)
    live.add_argument('--geometry',required=True)
    live.add_argument('--device',default='cpu')
    live.add_argument('--out',default='outputs/live_session.csv')
    live.add_argument('--save-video',default=None)
    live.add_argument('--no-window',action='store_true')
    record=sub.add_parser('record',help='Ghi một phiên camera gốc (chưa gán nhãn)')
    record.add_argument('--source',type=int,default=0)
    record.add_argument('--out',required=True)
    record.add_argument('--seconds',type=float,default=20)
    extract=sub.add_parser('extract',help='Trích khung hình từ video để gán nhãn')
    extract.add_argument('--video',required=True)
    extract.add_argument('--session',required=True)
    extract.add_argument('--root',default='data/labeled')
    extract.add_argument('--stride',type=int,default=8)
    ann=sub.add_parser('annotate',help='Gán ba điểm đặc trưng cho ảnh đã trích')
    ann.add_argument('--folder',default=None)
    ann.add_argument('--video',default=None)
    ann.add_argument('--dataset',default='datasets/mechanism')
    ann.add_argument('--split',choices=['train','val'],default='train')
    ann.add_argument('--session',default=None)
    ann.add_argument('--stride',type=int,default=10)
    split=sub.add_parser('split',help='Chia dữ liệu điểm đặc trưng thành train/val/test theo phiên độc lập')
    split.add_argument('--root',default='data/labeled')
    split.add_argument('--out',default='data/pose_dataset')
    split.add_argument('--seed',type=int,default=42)
    train=sub.add_parser('train',help='Tinh chỉnh YOLO Pose trên dữ liệu đã gán nhãn')
    train.add_argument('--data',default='data/pose_dataset/data.yaml')
    train.add_argument('--model',default='yolo11n-pose.pt')
    train.add_argument('--epochs',type=int,default=80)
    train.add_argument('--imgsz',type=int,default=640)
    train.add_argument('--batch',type=int,default=8)
    train.add_argument('--device',default=None)
    val=sub.add_parser('validate',help='Đánh giá điểm đặc trưng bằng Ultralytics trên tập giữ lại')
    val.add_argument('--data',default='data/pose_dataset/data.yaml')
    val.add_argument('--weights',required=True)
    val.add_argument('--split',choices=['val','test'],default='test')
    val.add_argument('--device',default=None)
    bench=sub.add_parser('keypoint-eval',help='Đánh giá điểm đặc trưng với nhãn thủ công độc lập')
    bench.add_argument('--data',default='data/pose_dataset')
    bench.add_argument('--detector',choices=['color','aruco','yolo'],default='yolo')
    bench.add_argument('--weights',default=None)
    bench.add_argument('--split',choices=['val','test'],default='test')
    bench.add_argument('--device',default='cpu')
    bench.add_argument('--out',default='outputs/keypoint_eval.json')
    er=sub.add_parser('evaluate-real',help='So sánh một CSV ước lượng với nhãn góc độc lập')
    er.add_argument('--session',required=True)
    er.add_argument('--ground-truth',required=True)
    er.add_argument('--out',default='outputs/real_evaluation.json')
    ab=sub.add_parser('real-ablation',help='So sánh công bằng ba phương pháp trên cùng quan sát thực')
    ab.add_argument('--session',required=True)
    ab.add_argument('--ground-truth',required=True)
    ab.add_argument('--geometry',required=True)
    ab.add_argument('--out',default='outputs/real_ablation')
    init_ds=sub.add_parser('init-dataset',help='Khởi tạo dữ liệu YOLO Pose ba điểm đặc trưng')
    init_ds.add_argument('--out',default='datasets/mechanism')
    ablate=sub.add_parser('ablate-real',help='Phát lại cả ba bộ ước lượng trên CÙNG luồng quan sát thực')
    ablate.add_argument('--session',required=True);ablate.add_argument('--geometry',required=True)
    ablate.add_argument('--ground-truth',required=True);ablate.add_argument('--out',default='outputs/real_ablation')
    demo=sub.add_parser('demo-video',help='Xuất video minh họa MP4 được ghi rõ là MÔ PHỎNG')
    demo.add_argument('--seconds',type=float,default=12.0);demo.add_argument('--out',default='outputs/synthetic_demo.mp4')
    descriptions={
        'seconds':'Thời lượng (giây)', 'fps':'Số khung hình mỗi giây',
        'out':'Đường dẫn đầu ra', 'seed':'Hạt giống ngẫu nhiên để tái lập',
        'noise':'Độ lệch chuẩn nhiễu mô phỏng (pixel)',
        'source':'Số hiệu camera hoặc đường dẫn video',
        'detector':'Bộ nhận diện: color (dấu màu), aruco (ArUco), yolo (YOLO Pose)',
        'weights':'Đường dẫn trọng số đã huấn luyện (.pt)',
        'geometry':'Tệp JSON hình học đã hiệu chuẩn',
        'device':'Thiết bị suy luận/huấn luyện, ví dụ cpu hoặc 0',
        'save_video':'Lưu video có lớp phủ tại đường dẫn này',
        'no_window':'Chạy không mở cửa sổ hiển thị',
        'video':'Đường dẫn video đầu vào', 'session':'Mã phiên hoặc tệp CSV phiên theo lệnh',
        'root':'Thư mục gốc dữ liệu', 'stride':'Khoảng cách lấy mẫu theo số khung hình',
        'folder':'Thư mục ảnh của một phiên để gán nhãn',
        'dataset':'Thư mục dữ liệu đích',
        'split':'Tập dữ liệu: train (huấn luyện), val (xác thực), test (kiểm tra)',
        'data':'Đường dẫn cấu hình hoặc thư mục dữ liệu theo lệnh',
        'model':'Trọng số khởi tạo YOLO Pose', 'epochs':'Số vòng huấn luyện',
        'imgsz':'Kích thước ảnh huấn luyện', 'batch':'Số ảnh mỗi lô',
        'ground_truth':'CSV góc tham chiếu độc lập theo mã khung hình',
    }
    for command in sub.choices.values():
        for action in command._actions:
            if not action.help:action.help=descriptions.get(action.dest)
    args=parser.parse_args(argv)

    if args.command=='gui':
        try:
            from .gui import launch
        except ImportError as exc:
            parser.error(f'Thiếu phụ thuộc giao diện: {exc}; hãy chạy pip install -e ".[gui]"')
        launch()
    elif args.command=='simulate':
        if args.seconds<=0 or args.fps<=0:parser.error('seconds và fps phải dương')
        geometry=Geometry();source=Simulator(geometry,SimConfig(seed=args.seed));tracker=MotionEKF(geometry)
        with SessionWriter(args.out) as writer:
            for _ in range(round(args.seconds*args.fps)):
                obs=source.step(1/args.fps)
                writer.write(obs,tracker.update(obs))
        print(f'Đã lưu phiên mô phỏng: {Path(args.out).resolve()}')
    elif args.command=='evaluate':
        result=run_evaluation(args.seconds,args.fps,args.seed,args.out,args.noise)
        print(json.dumps(result,ensure_ascii=False,indent=2))
    elif args.command=='markers':
        from .detection import create_aruco_sheet
        print(create_aruco_sheet(args.out))
    elif args.command=='calibrate':
        from .calibration import calibrate_interactively
        geo=calibrate_interactively(int(args.source) if args.source.isdigit() else args.source,args.out)
        print(json.dumps(vars(geo),indent=2))
    elif args.command=='live':
        from .live import run_live
        result=run_live(int(args.source) if args.source.isdigit() else args.source,
                        args.geometry,args.detector,args.weights,args.device,
                        args.out,not args.no_window,args.save_video)
        print(f'Đã lưu phiên camera/video: {result}')
    elif args.command=='record':
        from .record import record_camera
        print(record_camera(args.source,args.out,args.seconds))
    elif args.command=='extract':
        from .dataset import extract_frames
        print(f'Đã trích {extract_frames(args.video,args.session,args.root,args.stride)} ảnh')
    elif args.command=='annotate':
        if args.video:
            if not args.session:parser.error('Cần --session khi dùng --video')
            from .dataset import annotate_video
            count=annotate_video(args.video,args.dataset,args.split,args.session,args.stride)
            print('Số khung hình đã gán nhãn:',count)
        elif args.folder:
            from .dataset import annotate_folder
            annotate_folder(args.folder)
        else:parser.error('annotate cần --video hoặc --folder')
    elif args.command=='split':
        from .dataset import split_by_session
        print(json.dumps(split_by_session(args.root,args.out,args.seed),indent=2))
    elif args.command=='train':
        from .train import train_pose
        train_pose(args.data,args.model,args.epochs,args.imgsz,args.batch,args.device)
    elif args.command=='validate':
        from .train import validate_pose
        validate_pose(args.weights,args.data,args.split,args.device)
    elif args.command=='evaluate-real':
        from .real_evaluation import evaluate_recording
        print(json.dumps(evaluate_recording(args.session,args.ground_truth,args.out),ensure_ascii=False,indent=2))
    elif args.command=='real-ablation':
        from .real_ablation import real_ablation
        print(json.dumps(real_ablation(args.session,args.ground_truth,args.geometry,args.out),ensure_ascii=False,indent=2))
    elif args.command=='init-dataset':
        from .dataset import initialize_dataset
        print(initialize_dataset(args.out))
    elif args.command=='ablate-real':
        from .replay import replay_real
        print(json.dumps(replay_real(args.session,args.geometry,args.ground_truth,args.out),indent=2))
    elif args.command=='demo-video':
        import cv2
        from .synthetic import draw_mechanism
        if args.seconds<=0:parser.error('--seconds phải dương')
        path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
        writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),30,(900,520))
        if not writer.isOpened():parser.error('Không khởi tạo được video MP4 đầu ra')
        try:
            geo=Geometry();sim=Simulator(geo)
            for _ in range(round(args.seconds*30)):
                obs=sim.step(1/30)
                writer.write(draw_mechanism(geo,obs.truth_theta,observation=obs))
        finally:writer.release()
        print('Video minh họa mô phỏng:',path.resolve())
    elif args.command=='keypoint-eval':
        from .real_evaluation import evaluate_keypoints
        result=evaluate_keypoints(args.data,args.detector,args.weights,args.split,args.device)
        p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
