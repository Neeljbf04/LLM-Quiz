# modules/visualize.py

import matplotlib
matplotlib.use("Agg")  # IMPORTANT: headless backend (no Tk needed)

import matplotlib.pyplot as plt
from pathlib import Path
from typing import Optional
import pandas as pd

PLOTS_DIR = Path("temp_plots")
PLOTS_DIR.mkdir(parents=True, exist_ok=True)

def line_plot(df: pd.DataFrame, x: str, y: str, filename: Optional[str] = None, caption: Optional[str] = None) -> dict:
    """
    Saves a line plot and returns dict with path and caption.
    This uses the Agg backend, so no Tk installation is required.
    """

    if filename is None:
        filename = f"plot_{x}_vs_{y}.png"

    path = PLOTS_DIR / filename

    plt.figure()
    plt.plot(df[x], df[y])
    plt.xlabel(x)
    plt.ylabel(y)
    if caption:
        plt.title(caption)

    plt.tight_layout()
    plt.savefig(path)
    plt.close()

    return {"path": str(path), "caption": caption or f"Line plot of {y} vs {x}"}
