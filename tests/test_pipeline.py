# tests/test_pipeline.py
import pytest
from modules.data_fetch import download_csv
from modules.data_clean import parse_dates, drop_na
from modules.visualize import line_plot
from modules.llm_engine import LLMEngine
from orchestrator import Orchestrator
from pathlib import Path
import pandas as pd

SAMPLE_PATH = Path("samples/sample.csv").resolve()

def test_download_local_csv():
    df = download_csv(str(SAMPLE_PATH))
    assert isinstance(df, pd.DataFrame)
    assert len(df) == 3
    assert "date" in df.columns and "value" in df.columns

def test_parse_dates_and_dropna():
    df = download_csv(str(SAMPLE_PATH))
    df = parse_dates(df, ["date"])
    assert pd.api.types.is_datetime64_any_dtype(df["date"])
    # no NA in this sample but ensure drop_na works
    df2 = df.copy()
    df2.loc[0, "value"] = None
    df2 = drop_na(df2, subset=["value"])
    assert len(df2) == 2

def test_visualize_saves_file(tmp_path):
    df = download_csv(str(SAMPLE_PATH))
    # provide explicit filename
    out = line_plot(df, "date", "value", filename="test_plot.png")
    assert "path" in out
    p = Path(out["path"])
    assert p.exists()
    # cleanup
    p.unlink()

def test_orchestrator_count_rows():
    llm = LLMEngine()
    orch = Orchestrator(llm)
    res = orch.run(f"count rows in {SAMPLE_PATH}")
    assert "analysis" in res
    assert res["analysis"]["rows"] == 3

def test_orchestrator_plot_flow():
    llm = LLMEngine()
    orch = Orchestrator(llm)
    res = orch.run(f"plot date vs value from {SAMPLE_PATH}")
    assert "plot" in res
    assert "path" in res["plot"]
