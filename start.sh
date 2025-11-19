#!/bin/bash
python -m playwright install chromium
uvicorn server:app --host 0.0.0.0 --port $PORT
