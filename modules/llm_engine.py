import os
import re
import json
import logging
import asyncio
from typing import Any, Dict, Optional
from pathlib import Path

from modules.schemas import Plan

logger = logging.getLogger("llm_engine")

# ============================================================
# Deterministic fallback small planner
# ============================================================

class DeterministicPlanner:
    def __init__(self, system_prompt_path: str = "system_prompt.txt"):
        self.system_prompt = (
            Path(system_prompt_path).read_text()
            if Path(system_prompt_path).exists() else ""
        )

    def generate_plan(self, query: str) -> Dict[str, Any]:
        q = query.strip().lower()
        import re

        m = re.search(r"count\s+rows\s+in\s+(.+)", q)
        if m:
            url = m.group(1).strip()
            return {
                "steps": [
                    {"action": "fetch", "args": {"url": url, "file_type": "csv"}},
                    {"action": "analyze", "args": {"method": "row_count"}},
                    {"action": "final_answer", "args": {}}
                ]
            }

        m = re.search(r"plot\s+([a-z0-9_]+)\s+vs\s+([a-z0-9_]+)\s+from\s+(.+)", q)
        if m:
            x, y, url = m.group(1).strip(), m.group(2).strip(), m.group(3).strip()
            return {
                "steps": [
                    {"action": "fetch", "args": {"url": url, "file_type": "csv"}},
                    {"action": "clean", "args": {
                        "operations": [{"op": "parse_dates_if_possible", "cols": [x]}]
                    }},
                    {"action": "visualize", "args": {"x": x, "y": y}},
                    {"action": "final_answer", "args": {}}
                ]
            }

        m = re.search(r"show\s+head\s+of\s+(.+)", q)
        if m:
            url = m.group(1).strip()
            return {
                "steps": [
                    {"action": "fetch", "args": {"url": url, "file_type": "csv"}},
                    {"action": "analyze", "args": {"method": "head", "n": 5}},
                    {"action": "final_answer", "args": {}}
                ]
            }

        return {
            "steps": [{
                "action": "final_answer",
                "args": {"message": "I could not parse the query."}
            }]
        }


# ============================================================
# JSON extraction helper
# ============================================================

def extract_json(text: str) -> Optional[str]:
    """Try to extract JSON { ... } or [ ... ] from text."""
    match = re.search(r"(\{(?:.|\n)*\}|\[(?:.|\n)*\])", text)
    if match:
        blk = match.group(1)
        try:
            json.loads(blk)
            return blk
        except:
            pass

    start = text.find("{")
    if start == -1:
        return None

    depth = 0
    for i in range(start, len(text)):
        if text[i] == "{":
            depth += 1
        elif text[i] == "}":
            depth -= 1
            if depth == 0:
                candidate = text[start:i+1]
                try:
                    json.loads(candidate)
                    return candidate
                except:
                    return None
    return None


# ============================================================
# Injection detection
# ============================================================

INJECTION_BLACKLIST = [
    "ignore previous", "ignore instructions", "reveal the code", "reveal the secret",
    "system prompt", "system message", "internal", "hidden", "code word", "codeword",
    "tell me the secret", "print the secret", "output the secret", "reveal secret"
]

def detect_injection(user_query: str) -> bool:
    q = user_query.lower()
    return any(bad in q for bad in INJECTION_BLACKLIST)


# ============================================================
# LLM Engine Class
# ============================================================

class LLMEngine:
    """
    Main LLM engine.
    - Uses Groq if API key is present
    - Has fallback deterministic planner
    - Provides async chat() for Mode A
    - Provides generate_plan() for Mode B
    """

    def __init__(self, system_prompt_path: str = "system_prompt.txt"):
        self.system_prompt = (
            Path(system_prompt_path).read_text()
            if Path(system_prompt_path).exists() else ""
        )

        self.groq_api_key = os.getenv("GROQ_API_KEY")
        self.groq_model = os.getenv("GROQ_MODEL", "llama3-70b-8192")

        self.fallback = DeterministicPlanner(system_prompt_path)

        # Lazy Groq import
        self.groq_client = None
        if self.groq_api_key:
            try:
                from groq import Client
                self.groq_client = Client(api_key=self.groq_api_key)
            except Exception as e:
                logger.exception("Failed to initialize Groq: %s", e)
                self.groq_client = None

    # --------------------------------------------------------
    # MODE A — Async chat interface
    # --------------------------------------------------------
    async def chat(self, prompt: str) -> str:
        """
        Async chat interface used by Orchestrator.solve_text().

        If Groq API is available, call it.
        If not, echo prompt (simple deterministic fallback).
        """

        # No Groq → trivial fallback
        if not self.groq_client:
            return prompt.strip()

        try:
            # Run Groq sync client in a thread
            loop = asyncio.get_event_loop()
            resp = await loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=256,
                    temperature=0
                )
            )

            # Extract text
            try:
                return resp.choices[0].message.content.strip()
            except:
                return str(resp)

        except Exception as e:
            raise RuntimeError(f"Groq chat call failed: {e}")

    # --------------------------------------------------------
    # MODE B — Plan generation
    # --------------------------------------------------------

    def generate_plan(self, query: str, max_tokens: int = 1024) -> Dict[str, Any]:

        if detect_injection(query):
            return {"steps": [
                {"action": "final_answer",
                 "args": {"message": "Query contains disallowed instructions."}}
            ]}

        # fallback if no Groq
        if not self.groq_client:
            return self.fallback.generate_plan(query)

        system_prompt = self.system_prompt.strip()
        instructions = (
            system_prompt +
            "\n\nYou MUST output ONLY JSON with this schema:\n"
            "{ \"steps\": [ {\"action\": \"fetch|clean|visualize|analyze|final_answer\", \"args\": {...}} ] }\n"
            "No explanations. No markdown. No other text.\n"
        )

        messages = [
            {"role": "system", "content": instructions},
            {"role": "user", "content": query}
        ]

        try:
            loop = asyncio.get_event_loop()
            resp = loop.run_in_executor(
                None,
                lambda: self.groq_client.chat.completions.create(
                    model=self.groq_model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=0
                )
            )
            resp = asyncio.get_event_loop().run_until_complete(resp)

            try:
                raw = resp.choices[0].message.content
            except:
                raw = str(resp)

            js = extract_json(raw)
            if not js:
                return {"steps": [
                    {"action": "final_answer",
                     "args": {"message": "Model did not return JSON."}}
                ]}

            parsed = json.loads(js)

            # validate schema
            try:
                plan = Plan.parse_obj(parsed)
            except Exception as e:
                logger.error("Plan validation failed: %s", e)
                return {"steps": [
                    {"action": "final_answer",
                     "args": {"message": "Plan validation failed."}}
                ]}

            return {"steps": [s.dict() for s in plan.steps]}

        except Exception as e:
            logger.exception("Groq error: %s", e)
            return self.fallback.generate_plan(query)

    # --------------------------------------------------------
    def validate_plan(self, plan: Any) -> bool:
        try:
            Plan.parse_obj(plan)
            return True
        except:
            return False
    async def chat_raw(self, prompt: str) -> str:
        """
        Low-level chat call that returns ONLY raw model text.
        """
        return await self.chat(prompt)
