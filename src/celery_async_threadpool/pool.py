import asyncio
import inspect
import threading

import celery.concurrency.thread
import celery.utils.log


logger = celery.utils.log.get_logger(__name__)


def _run_on_loop(loop, async_fn):
    def _wrapped_async_fn(*args, **kwargs):
        coro = async_fn(*args, **kwargs)
        return asyncio.run_coroutine_threadsafe(coro, loop).result()

    return _wrapped_async_fn


class TaskPool(celery.concurrency.thread.TaskPool):
    # Attributes present in parent classes.
    app: celery.Celery
    # New attributes for this class.
    loop: asyncio.events.AbstractEventLoop
    loop_thread: threading.Thread

    def __init__(self, *args, **kwargs) -> None:
        # Call TaskPool's init which sets up a ThreadPoolExecutor.
        super().__init__(*args, **kwargs)
        # Start a fresh event loop on a new dedicated thread.
        self.loop = asyncio.events.new_event_loop()
        loop_thread = threading.Thread(
            target=self.loop.run_forever, name="celery-event-loop", daemon=True
        )
        # Start the thread and loop.
        loop_thread.start()
        # TODO: necessary? Probably doesn't hurt but we only plan to run async code via our
        # wrapper. This celery thread shouldn't be doing any 'await's on its own?
        asyncio.events.set_event_loop(self.loop)

        # Patch async tasks to run in our loop.
        tasks: dict[str, celery.Task] = self.app.tasks
        for name, task in tasks.items():
            # TODO: support for custom task.__call__'s that don't call task.run?
            if inspect.iscoroutinefunction(task.run):
                logger.info(f"Patching async Celery task: {name}")
                # Preserve original somwhere.
                setattr(task, "_async_run", task.run)
                # Overwrite task's run method with our wrapper.
                task.run = _run_on_loop(self.loop, task.run)


# TODO:
# - shutdown the loop nicely?
# - user provided startup fn (or use celery signal?)
# - user provided shutdown fn
