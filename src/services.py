from typing import Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)


def simple_search(query: str, df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["Описание", "Категория"])

    q = str(query).lower().strip()
    if not q:
        return pd.DataFrame(columns=["Описание", "Категория"])

    col = "Описание"
    if col not in df.columns:
        return pd.DataFrame(columns=["Описание", "Категория"])

    normalized = (
        df[col]
        .astype(str)
        .str.lower()
        .str.strip()
    )

    mask = normalized.str.contains(q, na=False)
    return df.loc[mask].copy()


def investment_bank(month_key: str, transactions: pd.DataFrame, threshold: int) -> float:
    """
    Считает накопления по «Инвесткопилке».
    """
    df = transactions.copy()

    # Проверка на корректность входных данных
    if "Дата операции" not in df.columns or df.empty:
        return 0.0

    if threshold <= 0:
        logger.warning("Invalid threshold value: %s", threshold)
        return 0.0

    if not pd.api.types.is_datetime64_any_dtype(df["Дата операции"]):
        df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")

    mask_month = df["Дата операции"].dt.strftime("%Y-%m") == month_key
    df_month = df[mask_month]

    spending = df_month[df_month["Сумма операции"] < 0]["Сумма операции"].abs()

    total_saved = 0.0
    for amount in spending:
        remainder = amount % threshold
        if remainder > 0:
            total_saved += threshold - remainder

    return round(float(total_saved), 2)
