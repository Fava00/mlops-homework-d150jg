"""Use earlier hours for training and later hours for evaluation."""
from pathlib import Path

import pandas as pd
import yaml

FEATURES = [
    'season', 'yr', 'mnth', 'hr', 'holiday', 'weekday', 'workingday',
    'weathersit', 'temp', 'atemp', 'hum', 'windspeed',
]


def chronological_split(frame: pd.DataFrame, test_start: str):
    ordered = frame.assign(dteday=pd.to_datetime(frame['dteday'])).sort_values(
        ['dteday', 'hr'], kind='stable'
    )
    before = ordered['dteday'] < pd.Timestamp(test_start)
    # An explicit feature list excludes identifiers, dates, and target components.
    columns = FEATURES + ['cnt']
    train, test = ordered.loc[before, columns], ordered.loc[~before, columns]
    if train.empty or test.empty:
        raise ValueError('test_start must leave observations on both sides of the split')
    return train, test


def prepare():
    params = yaml.safe_load(Path('params.yaml').read_text())['prepare']
    train, test = chronological_split(pd.read_csv('data/hour.csv'), params['test_start'])
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    for name, frame in [('train', train), ('test', test)]:
        frame.to_csv(f'data/processed/{name}.csv', index=False, lineterminator='\n')
    print(f'Chronological split: {len(train)} train / {len(test)} test rows')
