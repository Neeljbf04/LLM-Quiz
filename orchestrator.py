import logging

logger = logging.getLogger("orchestrator")

class Orchestrator:
    def __init__(self, llm_engine):
        self.llm = llm_engine

    async def solve_text(self, question_text: str, quiz_url: str):
        """
        Step A – simplest mode.
        LLM receives only the question text and returns final answer.
        """
        logger.info("Step A: Sending question to LLM...")

        prompt = f"""
You are an expert analysis assistant.

A quiz question is shown below. 
Respond ONLY with a JSON object of the form:

{{"answer": <final answer>}}

Do NOT include explanations. Only JSON.

Question:
{question_text}
"""

        try:
            raw = await self.llm.chat_raw(prompt)
        except Exception as ex:
            raise RuntimeError(f"LLM failed: {ex}")

        # Try to parse JSON
        import json
        try:
            parsed = json.loads(raw)
        except:
            # If the model returned plain text, wrap it
            parsed = {"answer": raw.strip()}

        return parsed
