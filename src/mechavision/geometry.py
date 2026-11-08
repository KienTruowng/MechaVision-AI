"""Calibrated planar slider-crank kinematics in image-pixel units.

Coordinate convention: crank angle is measured from the positive slider-axis
in the local x/y-up plane. The piston joint moves on y=slider_offset_px.
Camera must be approximately perpendicular to the motion plane. All distance
parameters must be measured for the *same physical joints* as the detections.
"""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
import math
import json
import numpy as np


@dataclass(frozen=True)
class Geometry:
    radius_px: float = 60.0
    rod_px: float = 180.0
    origin_x: float = 260.0
    origin_y: float = 240.0
    axis_deg: float = 0.0
    slider_offset_px: float = 0.0

    def __post_init__(self):
        vals = (self.radius_px,self.rod_px,self.origin_x,self.origin_y,self.axis_deg,self.slider_offset_px)
        if not all(math.isfinite(v) for v in vals):
            raise ValueError("Geometry values must be finite")
        if self.radius_px <= 0 or self.rod_px <= abs(self.slider_offset_px)+self.radius_px:
            raise ValueError("Full-rotation slider crank requires rod_px > abs(offset_px) + radius_px > 0")

    @property
    def origin(self) -> np.ndarray:
        return np.array([self.origin_x,self.origin_y],dtype=float)

    def image(self,x:float,y:float,origin:np.ndarray|None=None)->np.ndarray:
        rad=math.radians(self.axis_deg)
        base=self.origin if origin is None else np.asarray(origin,dtype=float)
        return base + np.array([math.cos(rad)*x+math.sin(rad)*y,
                                math.sin(rad)*x-math.cos(rad)*y])

    def local(self,pixel:np.ndarray,origin:np.ndarray|None=None)->np.ndarray:
        rad=math.radians(self.axis_deg)
        delta=np.asarray(pixel,dtype=float)-(self.origin if origin is None else origin)
        return np.array([math.cos(rad)*delta[0]+math.sin(rad)*delta[1],
                         math.sin(rad)*delta[0]-math.cos(rad)*delta[1]])

    def slider_x(self,theta:float)->float:
        r,l,e=self.radius_px,self.rod_px,self.slider_offset_px
        return r*math.cos(theta)+math.sqrt(max(0.0,l*l-(e-r*math.sin(theta))**2))

    def slider_dx_dtheta(self,theta:float)->float:
        r,l,e=self.radius_px,self.rod_px,self.slider_offset_px
        s,c=math.sin(theta),math.cos(theta)
        d=e-r*s
        return -r*s+(d*r*c)/math.sqrt(max(1e-12,l*l-d*d))

    def points(self,theta:float,origin:np.ndarray|None=None)->dict[str,np.ndarray]:
        return {"pivot":self.origin if origin is None else np.asarray(origin,dtype=float),
                "crank":self.image(self.radius_px*math.cos(theta),self.radius_px*math.sin(theta),origin),
                "piston":self.image(self.slider_x(theta),self.slider_offset_px,origin)}

    def theta_from_crank(self,point:np.ndarray,origin:np.ndarray|None=None)->float:
        x,y=self.local(point,origin)
        return math.atan2(y,x)

    def to_json(self,path:str|Path):
        p=Path(path);p.parent.mkdir(parents=True,exist_ok=True)
        p.write_text(json.dumps(asdict(self),indent=2),encoding="utf-8")

    @classmethod
    def from_json(cls,path:str|Path)->Geometry:
        return cls(**json.loads(Path(path).read_text(encoding="utf-8")))

    @classmethod
    def from_landmarks(cls,pivot,crank,piston,axis_point)->Geometry:
        """Calibrate from clicked joint centers at one known pose.

        axis_point establishes positive motion axis from the fixed pivot; it
        need not lie on the piston rail. Geometry can only be trusted if the
        selected piston point is the actual connecting-rod joint.
        """
        O=np.asarray(pivot,dtype=float)
        P=np.asarray(crank,dtype=float)
        S=np.asarray(piston,dtype=float)
        A=np.asarray(axis_point,dtype=float)
        d=A-O
        n=np.linalg.norm(d)
        if n<4:raise ValueError("Axis direction point too close to pivot")
        d/=n
        # image local x along d, local positive y to image-up side of d
        transverse=np.array([d[1],-d[0]])
        e=float(np.dot(S-O,transverse))
        r=float(np.linalg.norm(P-O))
        l=float(np.linalg.norm(S-P))
        a=math.degrees(math.atan2(d[1],d[0]))
        geo=cls(radius_px=r,rod_px=l,origin_x=float(O[0]),origin_y=float(O[1]),
                axis_deg=a,slider_offset_px=e)
        # If connecting rod is on the negative branch or geometry wrong, reject.
        theta=geo.theta_from_crank(P)
        err=abs(geo.local(S)[0]-geo.slider_x(theta))
        if err>max(4.0,0.04*l):
            raise ValueError(f"Geometry incompatible (piston projection residual {err:.1f}px). "
                             "Reverse axis direction, or select correct joint centers.")
        return geo


def wrap_angle(angle:float)->float:
    return math.atan2(math.sin(angle),math.cos(angle))


def nearest_angle(angle_wrapped:float,reference:float)->float:
    return reference+wrap_angle(angle_wrapped-reference)
