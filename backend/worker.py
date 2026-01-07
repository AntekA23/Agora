"""
ARQ Worker for processing background tasks.

Run with: arq app.services.task_queue.WorkerSettings
"""
from app.services.task_queue import WorkerSettings

# This file allows running the worker with:
# python -m arq worker.WorkerSettings
# or
# arq worker.WorkerSettings

__all__ = ["WorkerSettings"]
