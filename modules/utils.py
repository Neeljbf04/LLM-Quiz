# modules/utils.py
from pathlib import Path
import logging
from typing import Any

def setup_logging(level: int = logging.INFO) -> None:
    fmt = "%(asctime)s %(levelname)s %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt)

def safe_write_text(path: str | Path, content: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)

def normalize_path(path: str) -> str:
    # support file:// and plain paths
    if path.startswith("file://"):
        return path[7:]
    return path
