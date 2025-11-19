# orchestrator.py
from modules.llm_engine import LLMEngine
from modules.data_fetch import download_csv
from modules.data_clean import drop_na, parse_dates
from modules.visualize import line_plot
from modules.utils import setup_logging
import logging
from typing import Any

logger = logging.getLogger("orchestrator")
setup_logging()

class Orchestrator:
    def __init__(self, llm_engine: LLMEngine):
        self.llm = llm_engine

    def run(self, query: str) -> dict:
        plan = self.llm.generate_plan(query)
        logger.info("Plan generated: %s", plan)

        if not self.llm.validate_plan(plan):
            logger.error("Plan failed validation")
            return {"error": "invalid_plan"}

        df = None
        last_plot = None
        analysis_result = None

        for step in plan:
            action = step.get("action")
            args = step.get("args", {})
            try:
                if action == "fetch":
                    df = download_csv(args["url"])
                    logger.info("Fetched data: %s rows", len(df))

                elif action == "clean":
                    ops = args.get("operations", [])
                    for o in ops:
                        op = o.get("op")
                        if op == "parse_dates_if_possible":
                            cols = o.get("cols", [])
                            df = parse_dates(df, cols)
                        elif op == "dropna":
                            subset = o.get("subset")
                            df = drop_na(df, subset)

                elif action == "visualize":
                    x = args["x"]
                    y = args["y"]
                    last_plot = line_plot(df, x, y)

                elif action == "analyze":
                    method = args.get("method")
                    if method == "row_count":
                        analysis_result = {"rows": int(len(df))}
                    elif method == "head":
                        n = int(args.get("n", 5))
                        analysis_result = {"head": df.head(n).to_dict(orient="records")}

                elif action == "final_answer":
                    if analysis_result is not None:
                        return {"analysis": analysis_result, "plot": last_plot}
                    if last_plot is not None:
                        return {"plot": last_plot}
                    return {"message": args.get("message", "Done")}

            except Exception as e:
                logger.exception("Step failed: %s", action)
                return {"error": "step_failed", "step": action, "reason": str(e)}

        return {"error": "no_final_output"}
