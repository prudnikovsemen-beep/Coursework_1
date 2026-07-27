import os
import tempfile
import pandas as pd
import pytest
from pathlib import Path
from src.utils import load_transactions


def test_load_transactions_coerce_bad_dates():
    # Данные с «плохими» датами
    data = {
        "Дата операции": ["не дата", "2024-01-01", "опять не дата"],
        "Сумма операции": [100, 200, 300],
        "Категория": ["Еда", "Продукты", "Еда"],
        "Описание": ["Пицца", "Молоко", "Торт"],
        "Номер карты": ["1234", "1234", "5678"],
    }
    df_raw = pd.DataFrame(data)

    # Создаём временный Excel-файл
    with tempfile.NamedTemporaryFile(mode="wb", suffix=".xlsx", delete=False) as tmp:
        file_path = tmp.name

    try:
        # Записываем Excel (engine обязателен)
        df_raw.to_excel(file_path, index=False, engine="openpyxl")

        result = load_transactions(file_path)

        # Проверяем: все строки должны остаться, плохие даты стали NaT
        assert len(result) == 3
        assert result["Дата операции"].isna().sum() == 2
        assert pd.notna(result["Дата операции"][1])
    finally:
        os.unlink(file_path)


def test_load_transactions_success(tmp_path):
    """Успешная загрузка корректного Excel-файла."""
    xlsx_path = tmp_path / "test_ops.xlsx"
    data = {
        "Дата операции": ["01.05.2024", "10.05.2024"],
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
    """В файле колонки названы с опечаткой — функция видит отсутствие нужных колонок и возвращает пустой DF."""
    xlsx_path = tmp_path / "bad_ops.xlsx"
    # Здесь намеренно опечатки в названиях колонок, чтобы сработала ветка `if missing:`
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
    """Файл существует, но это не валидный Excel — функция должна обработать ошибку и вернуть пустой DF."""
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


def test_load_transactions_valid_columns_bad_data(tmp_path):
    # Импорты здесь не нужны — они уже есть вверху файла
    xlsx_path = tmp_path / "bad_ops.xlsx"

    data = {
        "Дата операции": ["не_дата", "2024-05-01", "31.12.2023"],
        "Сумма операции": ["abc", "100.5", "xyz"],
    }
    df_in = pd.DataFrame(data)
    df_in.to_excel(xlsx_path, index=False)

    df_out = load_transactions(xlsx_path)

    assert isinstance(df_out, pd.DataFrame)
    # Строка 0 (оба значения мусорные) удаляется dropna(how="all") → остаются 2 строки
    assert len(df_out) == 2

    assert pd.api.types.is_datetime64_any_dtype(df_out["Дата операции"])
    assert pd.api.types.is_numeric_dtype(df_out["Сумма операции"])

    # Проверка содержимого
    assert not pd.isna(df_out.iloc[0]["Дата операции"])
    assert not pd.isna(df_out.iloc[0]["Сумма операции"])

    assert not pd.isna(df_out.iloc[1]["Дата операции"])
    assert pd.isna(df_out.iloc[1]["Сумма операции"])
