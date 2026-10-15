"""Query data lineage, register an evaluated run, and resolve an alias."""
import argparse
import json
import re
import sys

import mlflow
from mlflow.tracking import MlflowClient

from .provenance import connect


def runs_for_data(client, experiment_id, md5):
    if not re.fullmatch(r'[0-9a-f]{32}', md5):
        raise ValueError('Expected a lowercase 32-character DVC MD5')
    runs = client.search_runs(
        [experiment_id], filter_string=f"tags.dvc_md5 = '{md5}'",
        order_by=['metrics.rmse ASC'], max_results=1000,
    )
    return [{
        'run_id': run.info.run_id, 'status': run.info.status,
        'params': run.data.params, 'metrics': run.data.metrics,
        'git_commit': run.data.tags.get('git_commit'),
        'data_remote_uri': run.data.tags.get('data_remote_uri'),
    } for run in runs]


def trace(client, name, alias):
    version = client.get_model_version_by_alias(name, alias)
    if not version.run_id:
        raise ValueError('Registered version has no source run_id')
    run = client.get_run(version.run_id)
    tags = run.data.tags
    return {
        'model_uri': f'models:/{name}@{alias}', 'version': version.version,
        'run_id': version.run_id, 'model_source': version.source,
        'params': run.data.params, 'metrics': run.data.metrics,
        'git_commit': tags['git_commit'], 'dvc_md5': tags['dvc_md5'],
        'data_remote_uri': tags['data_remote_uri'], 'data_endpoint': tags['data_endpoint'],
    }


def register(client, run_id, name, alias):
    run = client.get_run(run_id)
    if run.info.status != 'FINISHED' or 'rmse' not in run.data.metrics:
        raise ValueError('Register a finished run with evaluation metrics')
    for tag in ('git_commit', 'dvc_md5', 'data_remote_uri', 'data_endpoint'):
        if not run.data.tags.get(tag):
            raise ValueError(f'Run is missing provenance tag: {tag}')
    version = mlflow.register_model(f'runs:/{run_id}/model', name)
    # Check persisted metadata before moving the public alias.
    version = client.get_model_version(name, version.version)
    if version.run_id != run_id:
        raise ValueError('Registered model version does not link to the requested run')
    client.set_model_version_tag(name, version.version, 'selection_metric', 'rmse')
    client.set_registered_model_alias(name, alias, version.version)
    return trace(client, name, alias)


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['runs-for-data', 'register', 'trace'])
    parser.add_argument('value', nargs='?')
    parser.add_argument('--name', default='bike-demand-random-forest')
    parser.add_argument('--alias', default='staging')
    args = parser.parse_args()
    if args.command != 'trace' and not args.value:
        parser.error('Supply a DVC MD5 or a run ID')
    connect()
    client = MlflowClient()
    if args.command == 'runs-for-data':
        import os
        experiment = client.get_experiment_by_name(os.getenv('MLFLOW_EXPERIMENT_NAME', 'bike-demand-hw1'))
        result = runs_for_data(client, experiment.experiment_id, args.value)
    elif args.command == 'register':
        result = register(client, args.value, args.name, args.alias)
    else:
        result = trace(client, args.name, args.alias)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
