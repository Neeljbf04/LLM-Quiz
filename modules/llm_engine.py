# modules/llm_engine.py
"""
Deterministic LLM planner stub.

This is a simple rule-based parser that recognizes a few query patterns and
returns a validated plan (list of steps). This is Mode A (no external LLM).
"""

from typing import List, Dict, Any
import re
from pathlib import Path

ALLOWED_ACTIONS = {"fetch", "clean", "visualize", "analyze", "final_answer"}

class LLMEngine:
    def __init__(self, system_prompt_path: str = "system_prompt.txt"):
        self.system_prompt = Path(system_prompt_path).read_text() if Path(system_prompt_path).exists() else ""
    
    def generate_plan(self, query: str) -> List[Dict[str, Any]]:
        """
        Returns a deterministic plan based on simple heuristics.
        Supported examples:
         - "count rows in <url>"
         - "plot <x> vs <y> from <url>"
         - "plot date vs value from samples/sample.csv"
        """
        q = query.strip().lower()
        # count rows
        m = re.search(r"count\s+rows\s+in\s+(.+)", q)
        if m:
            url = m.group(1).strip()
            return [
                {"action": "fetch", "args": {"url": url, "file_type": "csv"}},
                {"action": "analyze", "args": {"method": "row_count"}},
                {"action": "final_answer", "args": {}}
            ]
        # plot x vs y from url
        m = re.search(r"plot\s+([a-z0-9_]+)\s+vs\s+([a-z0-9_]+)\s+from\s+(.+)", q)
        if m:
            x = m.group(1).strip()
            y = m.group(2).strip()
            url = m.group(3).strip()
            return [
                {"action": "fetch", "args": {"url": url, "file_type": "csv"}},
                {"action": "clean", "args": {"operations": [{"op": "parse_dates_if_possible", "cols": [x]}]}},
                {"action": "visualize", "args": {"x": x, "y": y}},
                {"action": "final_answer", "args": {}}
            ]
        # fallback: try fetch and show head
        m = re.search(r"show\s+head\s+of\s+(.+)", q)
        if m:
            url = m.group(1).strip()
            return [
                {"action": "fetch", "args": {"url": url, "file_type": "csv"}},
                {"action": "analyze", "args": {"method": "head", "n": 5}},
                {"action": "final_answer", "args": {}}
            ]

        # default - safe refusal plan
        return [
            {"action": "final_answer", "args": {"message": "I could not parse the query into a supported plan. Please use patterns like 'count rows in <path>' or 'plot date vs value from <path>'."}}
        ]

    def validate_plan(self, plan: List[Dict[str, Any]]) -> bool:
        # Ensure each step has an allowed action
        if not isinstance(plan, list):
            return False
        for s in plan:
            a = s.get("action")
            if a not in ALLOWED_ACTIONS:
                return False
        return True
