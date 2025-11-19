# main.py
from modules.llm_engine import LLMEngine
from orchestrator import Orchestrator
import argparse
import json

def cli():
    parser = argparse.ArgumentParser(description="LLM Analysis Quiz - Deterministic Mode")
    parser.add_argument("--query", "-q", type=str, help="Query string to analyze", required=False)
    args = parser.parse_args()

    if args.query:
        query = args.query
    else:
        query = input("Enter quiz query: ").strip()

    llm = LLMEngine()
    orchestrator = Orchestrator(llm)
    result = orchestrator.run(query)
    print(json.dumps(result, indent=2, default=str))

if __name__ == "__main__":
    cli()
