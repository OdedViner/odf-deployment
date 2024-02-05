import logging


def setup_logger():
    # Create logger
    log = logging.getLogger(__name__)

    # Set logging level
    log.setLevel(logging.INFO)

    # Create console handler and set level
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Create formatter and add it to the handler
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    console_handler.setFormatter(formatter)

    # Add handler to the logger
    log.addHandler(console_handler)

    # Disable propagation to higher-level loggers
    log.propagate = False

    return log
