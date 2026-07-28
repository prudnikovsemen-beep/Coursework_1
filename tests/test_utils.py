import os
import tempfile
from pathlib import Path

import pandas as pd

from src.utils import load_transactions


def test_load_transactions_coerce_bad_dates():
    """
    Проверяем, что плохие даты становятся NaT, а строки с NaT удаляются.
    Ожидаем: только 1 строка с валидной датой.
    """
    data = {
        "Дата операции": ["не дата", "2024-01-01", "опять не дата"],
        "Сумма операции": [100, 200, 300],
        "Категория": ["Еда", "Продукты", "Еда"],
        "Описание": ["Пицца", "Молоко", "Торт"],
        "Номер карты": ["1234", "1234", "5678"],
    }
    df_raw = pd.DataFrame(data)

    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xlsx", delete=False) as tmp:
        file_path = tmp.name

    try:
        df_raw.to_excel(file_path, index=False, engine="openpyxl")

        result = load_transactions(file_path)

        # Ожидаем: только 1 строка, где дата валидна
        assert len(result) == 1

        assert not pd.isna(result["Дата операции"].iloc[0])
        assert not pd.isna(result["Сумма операции"].iloc[0])
    finally:
        os.unlink(file_path)


def test_load_transactions_success(tmp_path):
    """Успешная загрузка корректного Excel-файла."""
    xlsx_path = tmp_path / "test_ops.xlsx"
    data = {
        "Дата операции": ["2024-05-01", "2024-05-10"],
        "Сумма операции": ["1000", "2500.50"],
    }
    df_in = pd.DataFrame(data)
    df_in.to_excel(xlsx_path, index=False)

    df_out = load_transactions(xlsx_path)

    assert len(df_out) == 2
    assert pd.api.types.is_datetime64_any_dtype(df_out["Дата операции"])
    assert pd.api.types.is_numeric_dtype(df_out["Сумма операции"])


def test_load_transactions_missing_file(tmp_path):
    """Файл не существует — функция возвращает пустой DataFrame с нужными колонками."""
    fake_path = tmp_path / "no_such_file.xlsx"
    df = load_transactions(fake_path)
    assert df.empty
    assert set(df.columns) == {"Дата операции", "Сумма операции"}


def test_load_transactions_bad_values(tmp_path):
    """В файле колонки названы с опечаткой — возвращаем пустой DF с нужными именами."""
    xlsx_path = tmp_path / "bad_ops.xlsx"
    data = {
        "Дата операция": ["не дата", "01.06.2024"],
        "Сумма операция": ["abc", "300"],
    }
    pd.DataFrame(data).to_excel(xlsx_path, index=False)

    df = load_transactions(xlsx_path)
    assert df.empty
    assert set(df.columns) == {"Дата операции", "Сумма операции"}


def test_load_transactions_missing_columns(tmp_path):
    """В файле вообще нет нужных колонок — возвращаем пустой DF с нужными именами."""
    xlsx_path = tmp_path / "wrong_cols.xlsx"
    data = {"A": [1, 2], "B": [3, 4]}
    pd.DataFrame(data).to_excel(xlsx_path, index=False)

    df = load_transactions(xlsx_path)
    assert df.empty
    assert set(df.columns) == {"Дата операции", "Сумма операции"}


def test_load_transactions_invalid_excel(tmp_path):
    """Файл существует, но это не валидный Excel — возвращаем пустой DF."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".xlsx", delete=False) as tmp:
        tmp.write("это не Excel, это просто текст")
        bad_path = Path(tmp.name)

    try:
        df = load_transactions(bad_path)
        assert isinstance(df, pd.DataFrame)
        assert df.empty
        assert set(df.columns) == {"Дата операции", "Сумма операции"}
    finally:
        if bad_path.exists():
            bad_path.unlink()


def test_load_transactions_corrupted_csv():
    """Тест на CSV, где данные не соответствуют ожидаемому формату."""
    # Импорты уже есть в начале файла — не дублируем их внутри теста
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp:
        tmp.write("Дата операции,Категория,Сумма\n")
        tmp.write("не_дата,Продукты,не_число\n")  # Мусорные данные
        tmp_path = tmp.name

    try:
        df = load_transactions(tmp_path)

        assert isinstance(df, pd.DataFrame)
        # Функция должна либо вернуть пустой DF, либо обработать ошибки
        assert df.empty or len(df) == 1
    finally:
        os.unlink(tmp_path)
