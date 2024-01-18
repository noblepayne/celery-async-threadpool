import subprocess

import pytest

from . import celery_app


# TODO: use regular celery fixture? threaded version? custom apps or queues? stop using sqlite?
@pytest.fixture
def celery_worker():
    process = subprocess.Popen(
        "celery -A tests.celery_app:app worker --pool custom --concurrency 1 --loglevel=ERROR",
        shell=True,
    )
    yield process
    process.terminate()
    process.wait()


def test_sync(celery_worker):
    result = celery_app.slow_ping.apply_async().wait()
    assert result == "pong"


def test_async(celery_worker):
    result = celery_app.slow_async_ping.apply_async().wait()
    assert result == "pong"
