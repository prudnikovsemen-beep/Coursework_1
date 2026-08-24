import logging
from pathlib import Path
from typing import Union

import pandas as pd

logger = logging.getLogger(__name__)


def get_greeting(hour: int) -> str:
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def load_transactions(file_path: Union[str, Path]) -> pd.DataFrame:
    file_path = Path(file_path)
    required_cols = ["Дата операции", "Сумма операции"]

    # Если файла нет — сразу пустой DF с нужными колонками
    if not file_path.exists():
        logger.error("Файл транзакций не найден: %s", file_path)
        return pd.DataFrame(columns=required_cols)

    try:
        # Читаем Excel; openpyxl должен быть в зависимостях проекта
        df = pd.read_excel(file_path, engine="openpyxl")
    except Exception as e:
        logger.exception("Ошибка чтения Excel-файла: %s", e)
        return pd.DataFrame(columns=required_cols)

    # Проверяем наличие обязательных колонок
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.warning(
            "В файле отсутствуют обязательные колонки: %s. Данные будут неполными.",
            missing,
        )
        return pd.DataFrame(columns=required_cols)

    # Приводим дату: без жёсткого формата, чтобы парсились разные варианты
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")

    # Приводим сумму к числу
    df["Сумма операции"] = pd.to_numeric(df["Сумма операции"], errors="coerce")

    # Удаляем строки, где нет даты ИЛИ нет суммы (достаточно одного NaN)
    df = df.dropna(subset=["Дата операции", "Сумма операции"])

    # Оставляем только нужные колонки
    df = df[required_cols]

    return df
