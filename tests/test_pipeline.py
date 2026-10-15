import pandas as pd
import pytest

from mlops_project.preparation import FEATURES, chronological_split
from mlops_project.evaluation import regression_metrics
from mlops_project.provenance import data_identity


def test_temporal_split_excludes_leakage_and_sorts_hours():
    frame = pd.DataFrame({name: [1, 2, 3, 4] for name in FEATURES})
    frame['dteday'] = ['2012-07-01', '2012-06-30', '2012-07-02', '2012-06-30']
    frame['hr'] = [0, 12, 0, 6]
    frame['cnt'] = [100, 200, 300, 400]
    frame['casual'] = frame['cnt']
    frame['registered'] = 0
    frame['instant'] = range(4)
    train, test = chronological_split(frame, '2012-07-01')
    assert train['cnt'].tolist() == [400, 200]
    assert test['cnt'].tolist() == [100, 300]
    assert list(train.columns) == FEATURES + ['cnt']
    with pytest.raises(ValueError, match='both sides'):
        chronological_split(frame, '2010-01-01')


def test_regression_metric_units():
    metrics = regression_metrics([0, 2], [1, 1])
    assert metrics == {'rmse': 1.0, 'mae': 1.0, 'r2': 0.0}


def test_training_rejects_data_not_matching_pointer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / 'data').mkdir()
    (tmp_path / 'data/hour.csv').write_text('changed bytes')
    (tmp_path / 'data/hour.csv.dvc').write_text('outs:\n- md5: wrong\n')
    with pytest.raises(ValueError, match='differs from its DVC pointer'):
        data_identity()
