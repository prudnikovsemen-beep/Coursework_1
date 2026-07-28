import os
import tempfile
import pandas as pd
from pathlib import Path
from src.utils import load_transactions


def test_load_transactions_coerce_bad_dates():
    """Проверяем, что плохие даты становятся NaT, но строки не удаляются сразу."""
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

        # Все 3 строки остаются, потому что нет dropna по сумме в этом тесте (логика проверяется отдельно)
        # Но здесь мы проверяем именно конвертацию дат
        assert len(result) == 3
        assert result["Дата операции"].isna().sum() == 2
        assert pd.notna(result["Дата операции"][1])
    finally:
        os.unlink(file_path)


def test_load_transactions_success(tmp_path):
    """Успешная загрузка корректного Excel-файла."""
    xlsx_path = tmp_path / "test_ops.xlsx"
    data = {
        # Используем формат, который точно парсится to_datetime без явного формата
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
    """В файле колонки названы с опечаткой — функция видит отсутствие нужных колонок и возвращает пустой DF."""
    xlsx_path = tmp_path / "bad_ops.xlsx"
    # Опечатка в названиях колонок: нет точного совпадения с required_cols
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
    """
    Проверяем очистку данных: оставляем только строки, где есть и валидная дата, и валидная сумма.
    Ожидаем: из 3 строк останется 2 валидные.
    """
    xlsx_path = tmp_path / "bad_ops.xlsx"

    # ИСПРАВЛЕНИЕ:
    # Строка 0: мусор (удалится)
    # Строка 1: валидно (останется)
    # Строка 2: валидно (останется)
    data = {
        "Дата операции": ["не_дата", "2024-05-01", "2024-12-31"],
        "Сумма операции": ["abc",      "100.5",      "200.0"],
    }
    df_in = pd.DataFrame(data)
    df_in.to_excel(xlsx_path, index=False)

    df_out = load_transactions(xlsx_path)

    assert isinstance(df_out, pd.DataFrame)
    # Должно остаться ровно 2 строки
    assert len(df_out) == 2

    assert pd.api.types.is_datetime64_any_dtype(df_out["Дата операции"])
    assert pd.api.types.is_numeric_dtype(df_out["Сумма операции"])

    # Проверяем, что в оставшихся строках НЕТ NaN
    assert not df_out["Дата операции"].isna().any()
    assert not df_out["Сумма операции"].isna().any()
