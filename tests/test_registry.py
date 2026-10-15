from types import SimpleNamespace

import pytest

from mlops_project.registry import register, runs_for_data, trace


def test_invalid_md5_rejected_before_query():
    with pytest.raises(ValueError, match='MD5'):
        runs_for_data(None, '1', "' OR 1=1")


def test_trace_rejects_broken_registry_link():
    client = SimpleNamespace(get_model_version_by_alias=lambda *args: SimpleNamespace(run_id=''))
    with pytest.raises(ValueError, match='no source run_id'):
        trace(client, 'bike-demand', 'staging')


def test_register_rejects_run_without_evaluation():
    run = SimpleNamespace(info=SimpleNamespace(status='FINISHED'), data=SimpleNamespace(metrics={}))
    client = SimpleNamespace(get_run=lambda _: run)
    with pytest.raises(ValueError, match='evaluation metrics'):
        register(client, 'run-id', 'bike-demand', 'staging')
