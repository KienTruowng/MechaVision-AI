from mechavision.geometry import Geometry
from mechavision.processing import Processor
from mechavision.synthetic import Simulator,SimConfig


def test_processor_log(tmp_path):
    geo=Geometry();sim=Simulator(geo,SimConfig(noise_px=0,outlier_rate=0))
    path=tmp_path/'session.csv'
    proc=Processor(geo,str(path))
    for i in range(7):
        metrics=proc.step(sim.step(1/30))
    proc.close()
    assert metrics['physics'].status in ('TRACKING','PREDICTED')
    assert len(path.read_text().splitlines())==8
