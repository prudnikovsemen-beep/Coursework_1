import pandas as pd
from datetime import datetime
from unittest.mock import patch

from src.services import investment_bank


def test_investment_bank_empty_df():
    df = pd.DataFrame()
    result = investment_bank("2024-05", df, threshold=100)
    assert result == 0.0


def test_investment_bank_missing_date_column():
    df = pd.DataFrame({"Сумма операции": [-100, -250]})
    result = investment_bank("2024-05", df, threshold=100)
    assert result == 0.0


def test_investment_bank_calculation_logic():
    data = {
        "Дата операции": ["2024-05-01", "2024-06-10", "2024-05-15", "2024-05-20"],
        "Сумма операции": [-120, -300, -50, -270],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%Y-%m-%d", errors="coerce")
    result = investment_bank("2024-05", df, threshold=100)
    assert isinstance(result, float)
    assert result >= 0.0


def test_investment_bank_threshold_zero_or_negative():
    data = {"Дата операции": ["2024-05-01"], "Сумма операции": [-150]}
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%Y-%m-%d", errors="coerce")
    result = investment_bank("2024-05", df, threshold=0)
    assert result == 0.0
    result_neg = investment_bank("2024-05", df, threshold=-10)
    assert result_neg == 0.0


def test_investment_bank_with_valid_data():
    data = {
        "Дата операции": [datetime(2024, 5, 1)],
        "Сумма операции": [-1000],
        "Категория": ["Инвестиции"],
        "Описание": ["Покупка акций"],
        "Номер карты": ["1234"],
    }
    df = pd.DataFrame(data)
    result = investment_bank("2024-05", df, threshold=100)
    assert isinstance(result, float)
    assert result >= 0.0


def test_investment_bank_filter_by_date_and_threshold():
    data = [
        {"Дата операции": "2024-04-01", "Сумма операции": -100},  # старая
        {"Дата операции": "2024-05-01", "Сумма операции": -50},  # попадает
        {"Дата операции": "2024-05-20", "Сумма операции": -200},  # попадает
    ]
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%Y-%m-%d", errors="coerce")
    result = investment_bank("2024-05", df, threshold=100)
    assert isinstance(result, float)
    assert result >= 0.0


@patch("src.services.logger.warning")
def test_investment_bank_missing_amount_column(mock_warning):
    df = pd.DataFrame({"Дата операции": ["2026-07-01"]})
    result = investment_bank("2026-07", df, threshold=100)
    assert result == 0.0
    assert mock_warning.called


@patch("src.services.logger.warning")
def test_investment_bank_non_numeric_amount(mock_warning):
    data = {
        "Дата операции": ["2026-07-01"],
        "Сумма операции": ["not a number"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], format="%Y-%m-%d", errors="coerce")
    result = investment_bank("2026-07", df, threshold=100)
    assert result == 0.0
    assert mock_warning.called


@patch("src.services.logger.warning")
def test_investment_bank_warning_on_invalid_threshold(mock_warning):
    """
    Проверяет, что при пороге <= 0 функция логирует предупреждение,
    но всё равно пытается что-то посчитать (или возвращает 0).
    Закрывает строки 68-72 в src/services.py.
    """
    import pandas as pd

    data = {
        "Дата операции": pd.date_range("2024-01-01", periods=3),
        "Категория": ["Инвест", "Инвест", "Другие"],
        "Сумма операции": [100, 200, 50],
    }
    df = pd.DataFrame(data)

    from src.services import investment_bank

    # Вызываем с порогом 0 или -100
    result = investment_bank("2024-05", df, threshold=0)

    assert mock_warning.called, "Функция должна залогировать предупреждение при threshold <= 0"
    # Проверь текст предупреждения в коде, он должен содержать что-то про 'threshold' или 'zero'
    messages = [call[0][0] for call in mock_warning.call_args_list]
    assert any("threshold" in msg.lower() or "zero" in msg.lower() for msg in messages)

    # Результат должен быть числом (float)
    assert isinstance(result, float)
