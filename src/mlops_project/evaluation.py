"""Evaluate later observations and attach the results to the training run."""
import json
from pathlib import Path

import joblib
import mlflow
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error


def regression_metrics(actual, predicted):
    return {
        'rmse': float(root_mean_squared_error(actual, predicted)),
        'mae': float(mean_absolute_error(actual, predicted)),
        'r2': float(r2_score(actual, predicted)),
    }


def evaluate():
    frame = pd.read_csv('data/processed/test.csv')
    model = joblib.load('models/model.joblib')
    metrics = regression_metrics(frame['cnt'], model.predict(frame.drop(columns='cnt')))
    run = json.loads(Path('models/run.json').read_text())
    # Use the server recorded by training, even if the current .env changed.
    mlflow.set_tracking_uri(run['tracking_uri'])
    with mlflow.start_run(run_id=run['run_id']):
        mlflow.log_metrics(metrics)
        mlflow.log_param('test_rows', len(frame))
    Path('metrics').mkdir(exist_ok=True)
    Path('metrics/metrics.json').write_text(json.dumps(metrics, indent=2) + '\n')
    print(json.dumps(metrics, indent=2))
