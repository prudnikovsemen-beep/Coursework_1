import logging
import pandas as pd

logger = logging.getLogger(__name__)


def investment_bank(month_key: str, transactions: pd.DataFrame, threshold: int) -> float:
    """
    Считает накопления по «Инвесткопилке».
    Возвращает 0.0 при любых проблемах с данными.
    """
    try:
        if transactions is None or transactions.empty:
            return 0.0

        required_cols = ["Дата операции", "Сумма операции"]
        if not all(col in transactions.columns for col in required_cols):
            logger.warning("Отсутствуют обязательные колонки в DataFrame")
            return 0.0

        df = transactions.copy()

        if threshold <= 0:
            logger.warning(
                "Порог threshold=%s некорректен (должен быть > 0). "
                "В расчётах используется минимальное значение 1.",
                threshold,
            )
            threshold = 1

        # Приводим дату к datetime, если ещё не
        if not pd.api.types.is_datetime64_any_dtype(df["Дата операции"]):
            df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")

        # Парсим месяц из month_key: '2024-05'
        try:
            year, month = map(int, month_key.split("-"))
        except Exception:
            logger.warning("Некорректный формат month_key: %s", month_key)
            return 0.0

        # Фильтр по месяцу — перенос внутри скобок, без W504
        mask_month = (
            (df["Дата операции"].dt.year == year)
            & (df["Дата операции"].dt.month == month)
        )
        df_filtered = df[mask_month]

        if df_filtered.empty:
            return 0.0

        # Конвертируем сумму, ошибки станут NaN
        df_filtered["Сумма операции"] = pd.to_numeric(
            df_filtered["Сумма операции"],
            errors="coerce",
        )

        nan_count = df_filtered["Сумма операции"].isna().sum()
        if nan_count > 0:
            logger.warning(
                "Обнаружено %d транзакций с невалидной суммой (NaN) — они будут исключены из расчёта.",
                nan_count,
            )

        # Удаляем строки с NaN в сумме
        df_filtered = df_filtered.dropna(subset=["Сумма операции"])

        # Применяем порог
        df_final = df_filtered[df_filtered["Сумма операции"] >= threshold]

        if df_final.empty:
            return 0.0

        return float(df_final["Сумма операции"].sum())

    except Exception as e:
        logger.exception("Ошибка в investment_bank: %s", e)
        return 0.0
