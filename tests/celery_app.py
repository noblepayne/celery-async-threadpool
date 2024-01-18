import asyncio
import celery
import time

app = celery.Celery(
    "test_app",
    broker="sqla+sqlite:///celerydb.sqlite3",
    backend="db+sqlite:///celerydb.sqlite3",
)

app.conf.update(
    {
        "task_serializer": "json",
        "result_serializer": "json",
    }
)


@app.task
def slow_ping(message: str = "pong"):
    time.sleep(2)
    return message


@app.task
async def slow_async_ping(message: str = "pong"):
    await asyncio.sleep(2)
    return message
