import logging
import os
from datetime import datetime

def setup_logger(name: str = "slimcheck") -> logging.Logger:
    """Setup logger that outputs to both console and file."""
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Avoid adding handlers multiple times
    if logger.handlers:
        return logger

    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # File handler
    SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
    log_dir = os.path.abspath(os.path.join(SCRIPT_DIR, "../../data/logs"))
    os.makedirs(log_dir, exist_ok=True)
    today = datetime.now().strftime("%Y%m%d")
    log_file = os.path.join(log_dir, f"{name}_{today}.log")
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

logger = setup_logger()
