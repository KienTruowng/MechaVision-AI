import cv2
import numpy as np
import pytest
from mechavision.dataset import _label_line,split_by_session


def test_label_visible_missing_format():
    line=_label_line([(10.,20.),None,(150.,100.)],(320,240))
    fields=list(map(float,line.split()))
    assert len(fields)==14
    assert fields[0]==0
    assert fields[7]==2 and fields[10]==0 and fields[13]==2


def test_session_disjoint_split(tmp_path):
    root=tmp_path/'labeled'
    for i in range(5):
        d=root/f'session{i}';d.mkdir(parents=True)
        cv2.imwrite(str(d/'000001.jpg'),np.full((100,120,3),80,dtype=np.uint8))
        (d/'000001.txt').write_text(_label_line([(20,20),(50,40),(80,60)],(120,100)))
    out=tmp_path/'pose'
    counts=split_by_session(str(root),str(out),seed=3)
    assert sum(counts.values())==5
    assert all(v>=1 for v in counts.values())
    manifest=(out/'split_manifest.json').read_text()
    assert 'session' in manifest
    assert (out/'data.yaml').exists()


def test_split_rejects_two_sessions(tmp_path):
    with pytest.raises(ValueError):split_by_session(str(tmp_path),str(tmp_path/'out'))
