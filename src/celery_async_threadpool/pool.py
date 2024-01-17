import celery.concurrency.thread


class TaskPool(celery.concurrency.thread.TaskPool):
    pass
