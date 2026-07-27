import pytest
import pandas as pd
from datetime import datetime, timedelta
from src.reports import spending_by_category


def test_spending_by_category_success():
    today = datetime.now()
    data = {
        "Дата операции": [
            today - timedelta(days=10),
            today - timedelta(days=20),
            today - timedelta(days=50),
        ],
        "Категория": ["Продукты", "Транспорт", "Продукты"],
        "Сумма операции": [-1000, -500, -2000],
        "Описание": ["Пятёрочка", "Такси", "Магнит"],
    }
    df = pd.DataFrame(data)

    result = spending_by_category(df)

    assert len(result) == 2

    products_row = result[result["Категория"] == "Продукты"]
    assert len(products_row) == 1
    assert products_row["Сумма"].iloc[0] == -3000.0

    transport_row = result[result["Категория"] == "Транспорт"]
    assert len(transport_row) == 1
    assert transport_row["Сумма"].iloc[0] == -500.0


def test_spending_by_category_empty_df():
    df = pd.DataFrame()
    result = spending_by_category(df)

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_spending_by_category_all_dates_nan():
    """Проверяем, что функция не падает, если все даты — NaT."""
    data = {
        "Дата операции": [pd.NaT, pd.NaT],
        "Категория": ["Продукты", "Такси"],
        "Сумма операции": [-100, -200],
    }
    df = pd.DataFrame(data)
    result = spending_by_category(df)

    assert isinstance(result, pd.DataFrame)
    # При NaT в датах маска по дате не сработает, filtered будет пустым, вернётся пустой DF
    assert result.empty or result["Сумма"].sum() == 0


def test_spending_by_category_missing_critical_columns():
    """Проверяем, что функция корректно выбрасывает ValueError, если нет обязательных колонок."""
    df = pd.DataFrame({"Другое": [1, 2, 3]})

    with pytest.raises(ValueError) as exc_info:
        spending_by_category(df)

    error_msg = str(exc_info.value)
    assert "Дата операции" in error_msg
    assert "Категория" in error_msg
    assert "Сумма операции" in error_msg


def test_spending_by_category_no_transactions_in_period():
    """Проверяем поведение, если за последние 90 дней нет транзакций."""
    data = {
        "Дата операции": [pd.Timestamp("2020-01-01")],  # очень старая дата
        "Категория": ["Продукты"],
        "Сумма операции": [-100],
    }
    df = pd.DataFrame(data)
    result = spending_by_category(df, date="2024-01-01")

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    # Здесь сработает ветка с предупреждением «Нет транзакций за последние 90 дней»


def test_spending_by_category_invalid_date_format():
    """Проверяем обработку некорректного формата даты."""
    data = {
        "Дата операции": [pd.Timestamp.now()],
        "Категория": ["Продукты"],
        "Сумма операции": [-100],
    }
    df = pd.DataFrame(data)

    with pytest.raises(ValueError):
        spending_by_category(df, date="не_дата")


def test_spending_by_category_filtered_empty():
    """Проверяем ветку, когда filtered пуст (нет транзакций за 90 дней)."""
    data = {
        "Дата операции": [pd.Timestamp("2020-01-01")],  # очень старая дата
        "Категория": ["Продукты"],
        "Сумма операции": [-100],
    }
    df = pd.DataFrame(data)
    result = spending_by_category(df, date="2024-01-01")

    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_spending_by_category_filtered_empty_with_warning(caplog):
    """Проверяем, что при пустом filtered возвращается пустой DF и пишется warning."""
    import logging
    caplog.set_level(logging.WARNING)

    data = {
        "Дата операции": [pd.Timestamp("2020-01-01")],
        "Категория": ["Продукты"],
        "Сумма операции": [-100],
    }
    df = pd.DataFrame(data)
    result = spending_by_category(df, date="2024-01-01")

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    # Проверяем, что warning реально был
    assert any("Нет транзакций за последние 90 дней" in record.message for record in caplog.records)
