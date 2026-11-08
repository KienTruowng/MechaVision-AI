"""MechaVision AI research CLI: live, calibration, dataset, training, evaluation."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from .geometry import Geometry
from .synthetic import Simulator,SimConfig
from .estimators import MotionEKF
from .evaluation import run_evaluation
from .session import SessionWriter


def main(argv=None):
    parser=argparse.ArgumentParser(prog='mechavision',description='MechaVision AI — physics-constrained visual state estimation')
    sub=parser.add_subparsers(dest='command',required=True)
    sim=sub.add_parser('simulate',help='Generate synthetic observations and CSV (not real evidence)')
    sim.add_argument('--seconds',type=float,default=12)
    sim.add_argument('--fps',type=int,default=30)
    sim.add_argument('--out',default='outputs/synthetic_session.csv')
    sim.add_argument('--seed',type=int,default=42)
    eva=sub.add_parser('evaluate',help='Reproducible synthetic ablation study')
    eva.add_argument('--seconds',type=float,default=24)
    eva.add_argument('--fps',type=int,default=30)
    eva.add_argument('--seed',type=int,default=42)
    eva.add_argument('--noise',type=float,default=3)
    eva.add_argument('--out',default='outputs/evaluation')
    sub.add_parser('gui',help='Start PySide6 dashboard (simulation + live camera)')
    markers=sub.add_parser('markers',help='Create printable ArUco marker sheet')
    markers.add_argument('--out',default='assets/aruco_markers.png')
    cal=sub.add_parser('calibrate',help='Four-click physical slider-crank calibration')
    cal.add_argument('--source',default='0',help='Camera integer or video path')
    cal.add_argument('--out',default='configs/geometry.json')
    live=sub.add_parser('live',help='Run measured camera/video tracking in OpenCV')
    live.add_argument('--source',default='0')
    live.add_argument('--detector',choices=['color','aruco','yolo'],default='color')
    live.add_argument('--weights',default=None)
    live.add_argument('--geometry',required=True)
    live.add_argument('--device',default='cpu')
    live.add_argument('--out',default='outputs/live_session.csv')
    live.add_argument('--save-video',default=None)
    live.add_argument('--no-window',action='store_true')
    record=sub.add_parser('record',help='Record a raw camera session (no labels)')
    record.add_argument('--source',type=int,default=0)
    record.add_argument('--out',required=True)
    record.add_argument('--seconds',type=float,default=20)
    extract=sub.add_parser('extract',help='Extract labeling frames from a video')
    extract.add_argument('--video',required=True)
    extract.add_argument('--session',required=True)
    extract.add_argument('--root',default='data/labeled')
    extract.add_argument('--stride',type=int,default=8)
    ann=sub.add_parser('annotate',help='Click three keypoints for extracted images')
    ann.add_argument('--folder',default=None)
    ann.add_argument('--video',default=None)
    ann.add_argument('--dataset',default='datasets/mechanism')
    ann.add_argument('--split',choices=['train','val'],default='train')
    ann.add_argument('--session',default=None)
    ann.add_argument('--stride',type=int,default=10)
    split=sub.add_parser('split',help='Create session-disjoint train/val/test pose dataset')
    split.add_argument('--root',default='data/labeled')
    split.add_argument('--out',default='data/pose_dataset')
    split.add_argument('--seed',type=int,default=42)
    train=sub.add_parser('train',help='Fine-tune a real YOLO pose model on labeled data')
    train.add_argument('--data',default='data/pose_dataset/data.yaml')
    train.add_argument('--model',default='yolo11n-pose.pt')
    train.add_argument('--epochs',type=int,default=80)
    train.add_argument('--imgsz',type=int,default=640)
    train.add_argument('--batch',type=int,default=8)
    train.add_argument('--device',default=None)
    val=sub.add_parser('validate',help='Ultralytics keypoint metrics on held-out test set')
    val.add_argument('--data',default='data/pose_dataset/data.yaml')
    val.add_argument('--weights',required=True)
    val.add_argument('--split',choices=['val','test'],default='test')
    val.add_argument('--device',default=None)
    bench=sub.add_parser('keypoint-eval',help='Independent manual-label keypoint evaluation')
    bench.add_argument('--data',default='data/pose_dataset')
    bench.add_argument('--detector',choices=['color','aruco','yolo'],default='yolo')
    bench.add_argument('--weights',default=None)
    bench.add_argument('--split',choices=['val','test'],default='test')
    bench.add_argument('--device',default='cpu')
    bench.add_argument('--out',default='outputs/keypoint_eval.json')
    er=sub.add_parser('evaluate-real',help='Compare one real estimate CSV with independent angle labels')
    er.add_argument('--session',required=True)
    er.add_argument('--ground-truth',required=True)
    er.add_argument('--out',default='outputs/real_evaluation.json')
    ab=sub.add_parser('real-ablation',help='Fair three-method comparison on the same real observations')
    ab.add_argument('--session',required=True)
    ab.add_argument('--ground-truth',required=True)
    ab.add_argument('--geometry',required=True)
    ab.add_argument('--out',default='outputs/real_ablation')
    init_ds=sub.add_parser('init-dataset',help='Initialize 3-keypoint YOLO Pose dataset')
    init_ds.add_argument('--out',default='datasets/mechanism')
    ablate=sub.add_parser('ablate-real',help='Replay all 3 estimators over the SAME real observation stream')
    ablate.add_argument('--session',required=True);ablate.add_argument('--geometry',required=True)
    ablate.add_argument('--ground-truth',required=True);ablate.add_argument('--out',default='outputs/real_ablation')
    demo=sub.add_parser('demo-video',help='Export an explicitly SYNTHETIC MP4 motion demo')
    demo.add_argument('--seconds',type=float,default=12.0);demo.add_argument('--out',default='outputs/synthetic_demo.mp4')
    args=parser.parse_args(argv)

    if args.command=='gui':
        try:
            from .gui import launch
        except ImportError as exc:
            parser.error(f'GUI dependencies missing: {exc}; install pip install -e ".[gui]"')
        launch()
    elif args.command=='simulate':
        if args.seconds<=0 or args.fps<=0:parser.error('seconds and fps must be positive')
        geometry=Geometry();source=Simulator(geometry,SimConfig(seed=args.seed));tracker=MotionEKF(geometry)
        with SessionWriter(args.out) as writer:
            for _ in range(round(args.seconds*args.fps)):
                obs=source.step(1/args.fps)
                writer.write(obs,tracker.update(obs))
        print(f'Synthetic session written: {Path(args.out).resolve()}')
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
        print(f'Live session written: {result}')
    elif args.command=='record':
        from .record import record_camera
        print(record_camera(args.source,args.out,args.seconds))
    elif args.command=='extract':
        from .dataset import extract_frames
        print(f'Extracted {extract_frames(args.video,args.session,args.root,args.stride)} images')
    elif args.command=='annotate':
        if args.video:
            if not args.session:parser.error('--session required with --video')
            from .dataset import annotate_video
            count=annotate_video(args.video,args.dataset,args.split,args.session,args.stride)
            print('Labeled frames:',count)
        elif args.folder:
            from .dataset import annotate_folder
            annotate_folder(args.folder)
        else:parser.error('annotate requires --video or --folder')
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
        if args.seconds<=0:parser.error('--seconds must be positive')
        path=Path(args.out);path.parent.mkdir(parents=True,exist_ok=True)
        writer=cv2.VideoWriter(str(path),cv2.VideoWriter_fourcc(*'mp4v'),30,(900,520))
        if not writer.isOpened():parser.error('Unable to initialize MP4 output')
        try:
            geo=Geometry();sim=Simulator(geo)
            for _ in range(round(args.seconds*30)):
                obs=sim.step(1/30)
                writer.write(draw_mechanism(geo,obs.truth_theta,observation=obs))
        finally:writer.release()
        print('Synthetic demo video:',path.resolve())
    elif args.command=='keypoint-eval':
        from .real_evaluation import evaluate_keypoints
        result=evaluate_keypoints(args.data,args.detector,args.weights,args.split,args.device)
        p=Path(args.out);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
        print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
