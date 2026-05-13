import logging
import os
from datetime import datetime
from config import LOG_DIR, OUTPUT_DIR


def setup_logger(name: str) -> logging.Logger:
    """Create a logger that writes to both console and a dated log file."""
    # FIX: Ensure /tmp/logs exists before writing (Vercel-safe)
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler (always works)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File handler — only add if /tmp is writable
    try:
        log_file = os.path.join(LOG_DIR, f"pipeline_{datetime.now():%Y%m%d}.log")
        fh = logging.FileHandler(log_file, encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except (OSError, PermissionError):
        # Silently skip file logging if filesystem is read-only (e.g. Vercel edge)
        pass

    return logger


def ensure_output_dir():
    """Create the /tmp/outputs folder if it doesn't exist."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def save_csv(df, filename: str, logger=None):
    """Save a DataFrame to /tmp/outputs and log the action."""
    ensure_output_dir()
    path = os.path.join(OUTPUT_DIR, filename)
    try:
        df.to_csv(path, index=False)
        if logger:
            logger.info(f"Saved {len(df):,} rows → {path}")
    except (OSError, PermissionError) as e:
        if logger:
            logger.warning(f"Could not save CSV to {path}: {e}")
    return path