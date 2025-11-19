import os
import re
import json
import asyncio
import logging
from typing import Optional
from urllib.parse import urljoin

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from dotenv import load_dotenv
from playwright.async_api import async_playwright
import httpx

from orchestrator import Orchestrator
from modules.llm_engine import LLMEngine


# -----------------------------------------------------
# Startup
# -----------------------------------------------------
load_dotenv()

SECRET_STRING = os.getenv("SECRET_STRING")
if not SECRET_STRING:
    raise RuntimeError("SECRET_STRING missing in .env")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger("server_async")

app = FastAPI(title="LLM Quiz Solver")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
async def health():
    return {"status": "ok"}

_playwright = None
_browser = None
orchestrator = None


class SolveRequest(BaseModel):
    email: str
    secret: str
    url: str


# -----------------------------------------------------
# HTML Helpers
# -----------------------------------------------------
async def extract_submit_url(page_html: str, base_url: str) -> Optional[str]:
    """
    Extract the submit URL from HTML. If missing, default to <origin>/submit
    """
    match = re.search(r'https?://[^\s"<>]+/submit', page_html, re.IGNORECASE)
    if match:
        return match.group(0).strip()

    # Fallback: the site ALWAYS uses "<origin>/submit"
    return urljoin(base_url, "/submit")


async def extract_question(page):
    """
    Try multiple selectors. Demo page has no question, so return None.
    """
    selectors = [
        ".question",
        "#question",
        "#question-text",
        ".quiz-question",
        "pre.question"
    ]

    for sel in selectors:
        try:
            el = await page.query_selector(sel)
            if el:
                txt = (await el.inner_text()).strip()
                if len(txt) > 0:
                    return txt
        except:
            continue

    # No question found = demo page
    return None


# -----------------------------------------------------
# Startup event
# -----------------------------------------------------
@app.on_event("startup")
async def startup_event():
    global _playwright, _browser, orchestrator

    logger.info("Starting server and Playwright (async) browser...")

    _playwright = await async_playwright().start()
    _browser = await _playwright.chromium.launch(headless=True)

    logger.info("Playwright browser launched (async).")

    orchestrator = Orchestrator(LLMEngine())

    logger.info("Orchestrator and LLM engine initialized.")


# -----------------------------------------------------
# Shutdown event
# -----------------------------------------------------
@app.on_event("shutdown")
async def shutdown_event():
    global _browser, _playwright

    if _browser:
        await _browser.close()
    if _playwright:
        await _playwright.stop()

    logger.info("Server shutdown complete.")


# -----------------------------------------------------
# /solve MAIN ENDPOINT
# -----------------------------------------------------
@app.post("/solve")
async def solve(req: SolveRequest):
    if req.secret != SECRET_STRING:
        raise HTTPException(403, "Invalid secret")

    quiz_url = req.url
    logger.info(f"Received quiz request: {quiz_url}")

    # Maximum 3 minutes
    start_time = asyncio.get_event_loop().time()

    while True:
        if asyncio.get_event_loop().time() - start_time > 180:
            raise HTTPException(500, "Exceeded 3-minute quiz time limit")

        page = await _browser.new_page()

        try:
            logger.info(f"Navigating to quiz page: {quiz_url}")
            await page.goto(quiz_url, timeout=60000)
            await page.wait_for_load_state("networkidle", timeout=60000)
            await asyncio.sleep(1)

            html = await page.content()
            question_text = await extract_question(page)

        except Exception as ex:
            raise HTTPException(500, f"Failed to load quiz page: {ex}")
        finally:
            await page.close()

        # ------------------------------
        # 1. Extract submit URL
        # ------------------------------
        submit_url = await extract_submit_url(html, quiz_url)
        logger.info(f"Submit URL resolved as: {submit_url}")

        # ------------------------------
        # 2. Prepare payload
        # ------------------------------
        payload = {
            "email": req.email,
            "secret": req.secret,
            "url": quiz_url,
            "answer": None
        }

        # ------------------------------
        # 3. Demo page → no question found
        # ------------------------------
        if question_text is None:
            logger.info("No question found — demo mode detected. Submitting dummy answer.")
            answer_value = "hello"
        else:
            # ------------------------------
            # 4. Solve using LLM orchestrator
            # ------------------------------
            logger.info("Running orchestrator on question text...")
            try:
                result = await orchestrator.solve_text(question_text, quiz_url)
                answer_value = result.get("answer", "")
            except Exception as ex:
                raise HTTPException(500, f"Orchestrator crashed: {ex}")

        payload["answer"] = answer_value
        logger.info(f"Prepared answer: {answer_value}")

        # ------------------------------
        # 5. Submit answer
        # ------------------------------
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(submit_url, json=payload)

            if resp.status_code not in (200, 201):
                raise HTTPException(
                    500,
                    f"Failed to submit answer: HTTP {resp.status_code} {resp.text}"
                )

            result = resp.json()
        except Exception as ex:
            raise HTTPException(500, f"Failed to submit answer: {ex}")

        logger.info(f"Submission result: {result}")

        # ------------------------------
        # 6. Continue quiz if needed
        # ------------------------------
        if result.get("correct") is True and result.get("url"):
            quiz_url = result["url"]
            logger.info(f"Next quiz URL: {quiz_url}")
            continue

        # Done
        return result
