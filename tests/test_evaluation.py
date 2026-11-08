from mechavision.evaluation import run_evaluation


def test_synthetic_ablation_outputs_and_labels(tmp_path):
    result=run_evaluation(seconds=4,fps=30,out_dir=tmp_path)
    assert result['metadata']['dataset']=='SYNTHETIC_ONLY'
    assert 'raw_cv_baseline' in result['methods']
    assert 'temporal_ekf' in result['methods']
    assert 'physics_ekf' in result['methods']
    assert (tmp_path/'ablation.csv').exists()
    assert (tmp_path/'summary.json').exists()
    assert all(0<=x['availability_pct']<=100 for x in result['methods'].values())
