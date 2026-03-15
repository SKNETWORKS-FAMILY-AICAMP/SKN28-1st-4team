import logging


def get_logger(name="predict_engine_research", level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )
    logger.addHandler(handler)
    logger.setLevel(level)
    logger.propagate = False
    return logger
