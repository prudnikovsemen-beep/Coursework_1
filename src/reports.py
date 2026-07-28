from functools import wraps
from pathlib import Path
from typing import Callable, Optional, Any, TypeVar

import pandas as pd
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

R = TypeVar("R")


def report_saver(
    filename: Optional[str] = None
) -> Callable[[Callable[..., pd.DataFrame]], Callable[..., pd.DataFrame]]:
    def decorator(func: Callable[..., pd.DataFrame]) -> Callable[..., pd.DataFrame]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> pd.DataFrame:
            result: pd.DataFrame = func(*args, **kwargs)

            base_name = filename or f"report_{func.__name__}.csv"
            reports_dir = Path("reports")
            reports_dir.mkdir(exist_ok=True)
            save_path = reports_dir / base_name

            if result.empty:
                logger.warning("Отчёт пуст: %s, файл не будет сохранён", func.__name__)
                return result

            try:
                result.to_csv(save_path, index=False, encoding="utf-8")
                logger.info("Отчёт сохранён: %s", save_path.absolute())
            except Exception as e:
                logger.exception("Ошибка при сохранении отчёта: %s", e)

            return result

        return wrapper

    return decorator


@report_saver()
def spending_by_category(
    transactions: pd.DataFrame,
    date: Optional[str] = None,
) -> pd.DataFrame:
    """
    Формирует отчёт по тратам по категориям за последние 90 дней.
    """
    if transactions.empty:
        return pd.DataFrame(columns=["Категория", "Сумма"])

    required_cols = ["Дата операции", "Категория", "Сумма операции"]
    missing = [c for c in required_cols if c not in transactions.columns]
    if missing:
        raise ValueError(f"В DataFrame отсутствуют обязательные колонки: {missing}")

    if date is None:
        ref_date = pd.Timestamp.now()
    else:
        try:
            ref_date = pd.to_datetime(date)
        except Exception as e:
            raise ValueError(f"Некорректный формат даты: {date}") from e

    start_date = ref_date - timedelta(days=90)
    col_name = "Дата операции"

    # Приводим к строке перед парсингом — это убирает ошибку to_datetime в Mypy
    if not pd.api.types.is_datetime64_any_dtype(transactions[col_name]):
        transactions = transactions.copy()  # чтобы не менять оригинал
        transactions[col_name] = pd.to_datetime(
            transactions[col_name].astype(str),
            format="%Y-%m-%d",
            errors="coerce",
        )

    mask_date = (transactions[col_name] >= start_date) & (
        transactions[col_name] <= ref_date
    )
    filtered = transactions.loc[mask_date].copy()

    if filtered.empty:
        logger.warning(
            "Нет транзакций за последние 90 дней до %s",
            ref_date.date(),
        )
        return pd.DataFrame(columns=["Категория", "Сумма"])

    spending = filtered[filtered["Сумма операции"] < 0]
    result = spending.groupby("Категория", dropna=True)["Сумма операции"].sum().reset_index()
    result.rename(columns={"Сумма операции": "Сумма"}, inplace=True)

    return result


def investment_bank(
    month_key: str,
    transactions: pd.DataFrame,
    threshold: int,
) -> float:
    """
    Считает накопления по «Инвесткопилке».
    """
    df = transactions.copy()
    col_name = "Дата операции"

    if col_name not in df.columns or df.empty:
        return 0.0

    if threshold <= 0:
        logger.warning("Invalid threshold value: %s", threshold)
        return 0.0

    if not pd.api.types.is_datetime64_any_dtype(df[col_name]):
        df[col_name] = pd.to_datetime(
            df[col_name].astype(str),
            format="%Y-%m-%d",
            errors="coerce",
        )

    if df[col_name].isna().all():
        logger.warning(
            "Не удалось распознать ни одной даты в колонке '%s'",
            col_name,
        )
        return 0.0

    mask_month = df[col_name].dt.strftime("%Y-%m") == month_key
    df_month = df[mask_month]

    spending = df_month[df_month["Сумма операции"] < 0]["Сумма операции"].abs()

    total_saved = 0.0
    for amount in spending:
        remainder = amount % threshold
        if remainder > 0:
            total_saved += threshold - remainder

    return round(float(total_saved), 2)


def simple_search(
    query: str,
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Простой поиск по колонке 'Описание'.
    """
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
