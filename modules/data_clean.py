# modules/data_clean.py
import pandas as pd
from typing import Iterable, Mapping, Optional

def drop_na(df: pd.DataFrame, subset: Optional[Iterable[str]] = None) -> pd.DataFrame:
    return df.dropna(subset=list(subset) if subset is not None else None)

def rename_cols(df: pd.DataFrame, mapping: Mapping[str, str]) -> pd.DataFrame:
    return df.rename(columns=mapping)

def parse_dates(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    for c in cols:
        df[c] = pd.to_datetime(df[c], errors='coerce')
    return df

def select_columns(df: pd.DataFrame, cols: Iterable[str]) -> pd.DataFrame:
    return df.loc[:, list(cols)]

def first_n_rows(df: pd.DataFrame, n: int) -> pd.DataFrame:
    return df.head(n)
