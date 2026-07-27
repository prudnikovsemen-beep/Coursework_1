import pandas as pd
from datetime import datetime
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
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    result = investment_bank("2024-05", df, threshold=100)

    # 120 → 80, 50 → 50, 270 → 30 → итого 160
    expected = 160.0
    assert result == expected


def test_investment_bank_threshold_zero_or_negative():
    data = {
        "Дата операции": ["2024-05-01"],
        "Сумма операции": [-150],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    # threshold <= 0 → функция должна вернуть 0.0 благодаря проверке внутри
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

    # Передаём все аргументы согласно сигнатуре функции
    result = investment_bank("2024-05", df, threshold=100)

    assert isinstance(result, float)
    # Для суммы 1000 и порога 100: остаток 0 → накоплено 0
    assert result == 0.0
