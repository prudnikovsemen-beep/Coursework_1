from functools import wraps
from pathlib import Path
from typing import Callable, Optional, Any
import pandas as pd
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


def report_saver(filename: Optional[str] = None):
    def decorator(func: Callable[..., pd.DataFrame]):
        @wraps(func)
        def wrapper(*args, **kwargs):
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
    date: Optional[str] = None
) -> pd.DataFrame:
    # ВАЖНО: сначала проверяем, пустой ли DataFrame — тогда сразу возвращаем пустой отчёт
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

    mask_date = (transactions["Дата операции"] >= start_date) & (transactions["Дата операции"] <= ref_date)
    filtered = transactions.loc[mask_date].copy()

    if filtered.empty:
        logger.warning("Нет транзакций за последние 90 дней до %s", ref_date.date())
        return pd.DataFrame(columns=["Категория", "Сумма"])

    spending = filtered[filtered["Сумма операции"] < 0]
    result = spending.groupby("Категория", dropna=True)["Сумма операции"].sum().reset_index()
    result.rename(columns={"Сумма операции": "Сумма"}, inplace=True)

    return result
