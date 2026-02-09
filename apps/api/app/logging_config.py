import logging
import sys
from pythonjsonlogger import jsonlogger
from app.config import settings
from app.context import request_id_ctx

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx.get()
        return True

def setup_logging():
    logger = logging.getLogger()
    # Clear existing handlers to avoid duplication
    if logger.handlers:
        logger.handlers.clear()
        
    logger.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    
    # Add Request ID filter
    handler.addFilter(RequestIdFilter())
    
    # Custom formatter to include standard fields and request_id
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
        rename_fields={"asctime": "timestamp", "levelname": "severity"}
    )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Set log level based on env
    if settings.ENV == "dev":
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)

    # Quiet down some noisy libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
