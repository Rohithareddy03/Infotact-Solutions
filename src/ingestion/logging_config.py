
"""Configure console and file logging for ingestion."""

import logging
from pathlib import Path


def configure_logging(
    log_dir: str | Path = "logs",
    level: int = logging.INFO,
) -> None:
    """Write ingestion logs to the console and a local log file."""
    directory = Path(log_dir)
    directory.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(
                directory / "ingestion.log",
                encoding="utf-8",
            ),
        ],
        force=True,
    )
