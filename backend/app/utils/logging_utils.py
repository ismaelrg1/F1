import logging
from typing import Optional


def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """Set up logging configuration for the entire project."""
    logger = logging.getLogger(name if name else __name__)

    # Prevent duplicates
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Format
        formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - [%(name)s] - %(message)s"
        )
        console_handler.setFormatter(formatter)

        logger.addHandler(console_handler)

        # Prevent propagation to root logger to avoid duplicate logs
        logger.propagate = False

    return logger
