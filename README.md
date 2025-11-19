# LLM Analysis Quiz — Deterministic Mode (Starter)

Quickstart:

1. Create and activate a Python 3.10+ virtualenv:
   - `python -m venv .venv && source .venv/bin/activate` (macOS/Linux)
   - `python -m venv .venv && .venv\Scripts\activate` (Windows)

2. Install dependencies:
   - `pip install -r requirements.txt`

3. Run tests:
   - `pytest -q`

4. Run CLI:
   - `python main.py`
     - Example query: `count rows in samples/sample.csv` or `plot date vs value from samples/sample.csv`

This repository uses a deterministic LLM planner stub (`modules/llm_engine.py`) intended for development and testing. Later you can replace it with a real LLM planner with strict JSON output validation.
