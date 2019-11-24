import logging
import logging.handlers
import sys

logger = logging.getLogger(__name__)


def configure_logging():
    logging.basicConfig(
        format="%(asctime)s : %(levelname)s : %(message)s",
        level=logging.INFO,
        stream=sys.stdout,
    )

    logger.debug("Logger initialized")


def reconfigure_logging(config):
    log_file = config["default"].get("log_file", None)
    if not log_file:
        logger.warning("Log file is not configured (conf file->default->log_file)")
    else:
        logger.info("Using log file %s", log_file)
        root_logger = logging.getLogger()
        h = logging.handlers.RotatingFileHandler(log_file, maxBytes=1024**3, backupCount=5)
        f = logging.Formatter("%(asctime)s : %(levelname)s : %(message)s")
        h.setFormatter(f)
        root_logger.addHandler(h)