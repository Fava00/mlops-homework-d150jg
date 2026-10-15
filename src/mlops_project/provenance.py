"""Connect a run to the exact dataset bytes and committed source."""
import hashlib
import os
from pathlib import Path
import subprocess

from dotenv import load_dotenv
from dvc.repo import Repo
import mlflow
import yaml


def connect():
    load_dotenv()
    mlflow.set_tracking_uri(os.getenv('MLFLOW_TRACKING_URI', 'http://127.0.0.1:5500'))
    mlflow.set_experiment(os.getenv('MLFLOW_EXPERIMENT_NAME', 'bike-demand-hw1'))


def data_identity():
    pointer = yaml.safe_load(Path('data/hour.csv.dvc').read_text())['outs'][0]
    actual = hashlib.md5(Path('data/hour.csv').read_bytes()).hexdigest()
    if actual != pointer['md5']:
        raise ValueError('Dataset differs from its DVC pointer; run dvc add before training')
    with Repo('.') as repo:
        remote = repo.config['remote'][repo.config['core']['remote']]
        uri = remote['url'].rstrip('/') + f'/files/md5/{actual[:2]}/{actual[2:]}'
        return {'dvc_md5': actual, 'data_remote_uri': uri,
                'data_endpoint': remote.get('endpointurl', '')}


def git_commit():
    return subprocess.check_output(['git', 'rev-parse', 'HEAD'], text=True).strip()
