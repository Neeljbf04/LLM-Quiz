# modules/data_fetch.py
import pandas as pd
import requests
from io import StringIO, BytesIO
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from .utils import normalize_path

DEFAULT_TIMEOUT = 15  # seconds
MAX_BYTES = 5 * 1024 * 1024  # 5 MB

def download_csv(url: str, timeout: int = DEFAULT_TIMEOUT) -> pd.DataFrame:
    """
    Supports:
      - http(s) URLs
      - file://local paths or direct local paths
    Returns pandas DataFrame.
    """
    url = normalize_path(url)
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        r = requests.get(url, timeout=timeout, stream=True)
        r.raise_for_status()
        # check content length if present
        cl = r.headers.get("content-length")
        if cl and int(cl) > MAX_BYTES:
            raise ValueError("file_too_large")
        # read up to MAX_BYTES
        raw = r.content
        if len(raw) > MAX_BYTES:
            raise ValueError("file_too_large")
        text = raw.decode("utf-8")
        return pd.read_csv(StringIO(text))
    else:
        # treat as local file
        p = Path(url)
        if not p.exists():
            raise FileNotFoundError(f"file_not_found:{url}")
        if p.stat().st_size > MAX_BYTES:
            raise ValueError("file_too_large")
        return pd.read_csv(p)

def download_json(url: str, timeout: int = DEFAULT_TIMEOUT):
    url = normalize_path(url)
    parsed = urlparse(url)
    if parsed.scheme in ("http", "https"):
        r = requests.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    else:
        p = Path(url)
        if not p.exists():
            raise FileNotFoundError(f"file_not_found:{url}")
        import json
        return json.loads(p.read_text())
