import csv
import math
from mechavision.geometry import Geometry
from mechavision.synthetic import Simulator,SimConfig
from mechavision.processing import Processor
from mechavision.real_ablation import real_ablation


def test_paired_real_ablation_on_common_observations(tmp_path):
    geo=Geometry();geo.to_json(tmp_path/'geo.json')
    sim=Simulator(geo,SimConfig(noise_px=.5,outlier_rate=0,seed=9))
    data=tmp_path/'observation.csv';truth=tmp_path/'reference.csv'
    proc=Processor(geo,str(data))
    with truth.open('w',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['frame','theta_deg']);writer.writeheader()
        for _ in range(80):
            obs=sim.step(1/30)
            proc.step(obs)
            writer.writerow({'frame':obs.frame_id,'theta_deg':math.degrees(obs.truth_theta)})
    proc.close()
    result=real_ablation(str(data),str(truth),str(tmp_path/'geo.json'),str(tmp_path/'report'))
    assert len(result['methods'])==3
    assert (tmp_path/'report'/'real_ablation.csv').exists()
    assert result['methods']['raw_visual']['coverage_pct']<100
    assert result['methods']['physics_ekf']['coverage_pct']>0
