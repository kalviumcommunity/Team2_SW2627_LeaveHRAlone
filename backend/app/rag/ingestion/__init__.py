import logging
from typing import Optional
from fastapi import BackgroundTasks

from app.rag.ingestion.pipeline import async_process_document, process_document_sync

logger = logging.getLogger(__name__)


def trigger_document_processing(
    document_id: str,
    background_tasks: Optional[BackgroundTasks] = None,
) -> None:
    """Trigger background document processing via BackgroundTasks or Celery."""
    if background_tasks is not None:
        background_tasks.add_task(async_process_document, str(document_id))
        return

    try:
        from app.rag.ingestion.tasks import process_document_task
        process_document_task.delay(str(document_id))
        logger.info("Queued document %s to Celery", document_id)
    except Exception as e:
        logger.warning("Celery queueing failed (%s). Executing synchronously.", e)
        process_document_sync(str(document_id))


__all__ = [
    "async_process_document",
    "process_document_sync",
    "trigger_document_processing",
]
