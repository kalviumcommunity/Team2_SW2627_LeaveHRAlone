import logging
from app.core.celery_app import celery
from app.rag.ingestion.pipeline import process_document_sync

logger = logging.getLogger(__name__)


@celery.task(name="process_document_task", bind=True, max_retries=2)
def process_document_task(self, document_id: str) -> bool:
    """Asynchronous Celery task for processing uploaded HR policy documents."""
    logger.info("Executing background document processing task for ID: %s", document_id)
    try:
        success = process_document_sync(document_id)
        if not success:
            raise RuntimeError(f"Pipeline returned failure for document {document_id}")
        return success
    except Exception as exc:
        logger.exception("Error in process_document_task: %s", exc)
        raise self.retry(exc=exc, countdown=10)
