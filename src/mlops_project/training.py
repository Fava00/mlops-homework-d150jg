"""Fit and log a Random Forest; evaluation adds metrics to the same run."""
import json
from pathlib import Path

import joblib
import mlflow
import mlflow.sklearn
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
import yaml

from .provenance import connect, data_identity, git_commit


def train():
    params = yaml.safe_load(Path('params.yaml').read_text())
    identity = data_identity()
    frame = pd.read_csv('data/processed/train.csv')
    x, y = frame.drop(columns='cnt'), frame['cnt']
    model = RandomForestRegressor(**params['train'], n_jobs=1)
    connect()
    with mlflow.start_run(run_name='random-forest') as run:
        mlflow.set_tags({**identity, 'git_commit': git_commit(), 'task': 'hourly-bike-demand'})
        mlflow.log_params(params['train'])
        mlflow.log_param('test_start', params['prepare']['test_start'])
        mlflow.log_param('train_rows', len(frame))
        model.fit(x, y)
        info = mlflow.sklearn.log_model(model, name='model', input_example=x.head(5))
        Path('models').mkdir(exist_ok=True)
        joblib.dump(model, 'models/model.joblib')
        Path('models/run.json').write_text(json.dumps({
            'run_id': run.info.run_id, 'model_uri': info.model_uri,
            'tracking_uri': mlflow.get_tracking_uri(), **identity,
        }, indent=2) + '\n')
        print(f'MLflow run: {run.info.run_id}')
