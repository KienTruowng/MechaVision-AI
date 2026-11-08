import math
import numpy as np
from mechavision.estimators import MotionEKF,RawVisualEstimator
from mechavision.geometry import Geometry,wrap_angle
from mechavision.synthetic import Simulator,SimConfig
from mechavision.types import Observation,Landmark


def test_estimator_tracks_clean_varying_motion():
    geo=Geometry()
    sim=Simulator(geo,SimConfig(noise_px=.3,outlier_rate=0,
                                crank_occlusion_rate=0,piston_occlusion_rate=0,seed=2))
    ekf=MotionEKF(geo)
    errors=[]
    for i in range(150):
        obs=sim.step(1/30);est=ekf.update(obs)
        if i>40 and est.theta is not None:
            errors.append(abs(math.degrees(wrap_angle(est.theta-obs.truth_theta))))
    assert np.median(errors)<1.5


def test_piston_rescues_short_crank_occlusion():
    geo=Geometry()
    tracker=MotionEKF(geo,physics=True)
    raw=RawVisualEstimator(geo)
    theta=.7
    for i in range(25):
        theta+=.035
        points=geo.points(theta)
        landmarks={name:Landmark(*p,confidence=.98) for name,p in points.items()}
        if 10<=i<16:landmarks.pop('crank')
        obs=Observation(i/30,landmarks)
        a=tracker.update(obs);b=raw.update(obs)
        if 10<=i<16:
            assert b.status=='LOST'
            assert a.status in ('TRACKING','PREDICTED')


def test_uncertainty_abstains_during_long_occlusion():
    geo=Geometry()
    ekf=MotionEKF(geo,max_prediction_sec=.25)
    points=geo.points(.3)
    obs=Observation(0,{k:Landmark(*v) for k,v in points.items()})
    assert ekf.update(obs).status=='TRACKING'
    assert ekf.update(Observation(.1,{})).status=='PREDICTED'
    lost=ekf.update(Observation(.65,{}))
    assert lost.status=='LOST'
    assert lost.theta is None


def test_reject_gross_outlier():
    geo=Geometry()
    ekf=MotionEKF(geo)
    for i in range(30):
        pts=geo.points(.35+i*.02)
        landmarks={k:Landmark(*v) for k,v in pts.items()}
        if i==20:landmarks['piston']=Landmark(1500,1500)
        est=ekf.update(Observation(i/30,landmarks))
        if i==20:assert est.rejected_count>=1
