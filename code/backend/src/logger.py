import logging
import json
import sys
import traceback
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """Formatter to output logs as structured JSON."""
    def format(self, record):
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Inject Trace ID if thread-local or context var has it
        # Relying on standard attributes passed via 'extra' dictionary
        if hasattr(record, "trace_id"):
            log_entry["trace_id"] = record.trace_id

        if record.exc_info:
            log_entry["exception"] = "".join(traceback.format_exception(*record.exc_info))

        return json.dumps(log_entry)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        # Output to stdout for 12-factor compliance
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger

# Main application logger
app_logger = get_logger("cpts421_backend")
