import csv
import json
from pathlib import Path
import pytest
from mechavision.dataset import yolo_pose_line,initialize_dataset
from mechavision.cli import main
from mechavision.real_evaluation import evaluate_recording


def test_pose_label_format_and_occlusion():
    line=yolo_pose_line([(100,100),None,(250,100)],640,480)
    fields=line.split()
    assert len(fields)==14
    assert fields[0]=='0'
    assert fields[8:11]==['0.000000','0.000000','0']
    with pytest.raises(ValueError):yolo_pose_line([None]*3,640,480)


def test_cli_full_pipeline(tmp_path,capsys):
    main(['simulate','--seconds','1','--fps','20','--out',str(tmp_path/'session.csv')])
    assert (tmp_path/'session.csv').is_file()
    with (tmp_path/'session.csv').open() as f:
        rows=list(csv.DictReader(f))
    assert len(rows)==20
    main(['evaluate','--seconds','2','--fps','20','--out',str(tmp_path/'eval')])
    result=json.loads((tmp_path/'eval'/'summary.json').read_text())
    assert 'physics_ekf' in result['methods']
    assert result['metadata']['dataset']=='SYNTHETIC_ONLY'


def test_dataset_and_real_evaluation(tmp_path):
    root=tmp_path/'data'
    assert initialize_dataset(root).is_file()
    session=tmp_path/'s.csv'
    session.write_text('frame,theta_rad,status\n1,0.5,TRACKING\n2,,LOST\n3,1.5,TRACKING\n')
    truth=tmp_path/'truth.csv'
    truth.write_text('frame,theta_rad\n1,0.52\n2,1.0\n3,1.48\n')
    report=evaluate_recording(str(session),str(truth))
    assert report['num_reference_frames']==3
    assert report['num_estimates']==2
    assert report['coverage_pct']==pytest.approx(66.6666667)


def test_real_ablation_replays_same_data(tmp_path):
    from mechavision.geometry import Geometry
    from mechavision.synthetic import Simulator,SimConfig
    from mechavision.estimators import MotionEKF
    from mechavision.session import SessionWriter
    from mechavision.replay import replay_real
    geo=Geometry();geo_file=tmp_path/'geometry.json';geo.to_json(geo_file)
    sim=Simulator(geo,SimConfig(noise_px=2.2,seed=33))
    session_file=tmp_path/'session.csv';reference=tmp_path/'gt.csv'
    rows=[]
    with SessionWriter(session_file) as writer:
        estimator=MotionEKF(geo)
        for _ in range(150):
            obs=sim.step(1/30)
            writer.write(obs,estimator.update(obs))
            rows.append((obs.frame_id,obs.truth_theta))
    with reference.open('w',newline='') as f:
        wr=csv.writer(f);wr.writerow(['frame','theta_rad']);wr.writerows(rows)
    result=replay_real(str(session_file),str(geo_file),str(reference),str(tmp_path/'report'))
    assert len(result['methods'])==3
    assert result['paired_frame_count']>0
    assert (tmp_path/'report'/'real_ablation.csv').is_file()
