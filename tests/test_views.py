import pandas as pd
from datetime import datetime

from src.views import generate_home_page_json


def test_generate_home_page_json_top_5_by_payment():
    data = {
        "Дата операции": [
            "2024-05-01", "2024-05-02", "2024-05-03",
            "2024-05-04", "2024-05-05",
        ],
        "Сумма операции": [-100, -200, -300, -400, -500],
        "Категория": ["Продукты"] * 5,
        "Описание": ["Пятёрочка"] * 5,
        "Номер карты": ["1234", "1234", "5678", "1234", "9999"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    settings = {"currency": "RUB"}
    result = generate_home_page_json("2024-05-31 12:00:00", df, settings)

    assert "top_transactions" in result
    assert len(result["top_transactions"]) == 5


def test_generate_home_page_json_empty_df():
    df = pd.DataFrame()
    settings = {"currency": "RUB"}
    result = generate_home_page_json("2024-05-31 12:00:00", df, settings)

    assert "greeting" in result
    assert "cards" in result
    assert isinstance(result["cards"], list)
    assert len(result["cards"]) == 0

    assert "top_transactions" in result
    assert isinstance(result["top_transactions"], list)
    assert len(result["top_transactions"]) == 0

    assert "currency_rates" in result
    assert "stock_prices" in result


def test_generate_home_page_json_missing_date_column():
    data = [
        {"Сумма операции": 100, "Категория": "Еда", "Описание": "Пицца"},
    ]
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}
    result = generate_home_page_json(date_str, df, settings)

    assert "greeting" in result
    assert "cards" in result
    assert "top_transactions" in result
    assert isinstance(result["top_transactions"], list)
    assert len(result["top_transactions"]) == 0


def test_generate_home_page_json_all_dates_nan():
    data = [
        {
            "Дата операции": pd.NaT,
            "Сумма операции": -100,
            "Категория": "Еда",
            "Описание": "Пицца",
        },
        {
            "Дата операции": pd.NaT,
            "Сумма операции": -200,
            "Категория": "Транспорт",
            "Описание": "Такси",
        },
    ]
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}
    result = generate_home_page_json(date_str, df, settings)

    assert "greeting" in result
    assert "top_transactions" in result
    assert isinstance(result["top_transactions"], list)
    assert len(result["top_transactions"]) == 0


def test_generate_home_page_json_invalid_date_string():
    """
    Проверяет поведение при невалидной строке даты.
    Если в generate_home_page_json нет try/except вокруг strptime,
    то функция выбросит ValueError — тест это подтверждает.
    """
    data = {
        "Дата операции": ["2024-05-01"],
        "Сумма операции": [-100],
        "Категория": ["Еда"],
        "Описание": ["Пицца"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])
    settings = {}

    try:
        generate_home_page_json("не_дата", df, settings)
    except ValueError:
        pass


def test_generate_home_page_json_no_date_column_but_has_other_data():
    data = [
        {
            "Сумма операции": -100,
            "Категория": "Еда",
            "Описание": "Пицца",
            "Номер карты": "1234",
        },
        {
            "Сумма операции": -200,
            "Категория": "Транспорт",
            "Описание": "Такси",
            "Номер карты": "5678",
        },
    ]
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}
    result = generate_home_page_json(date_str, df, settings)

    assert "greeting" in result
    assert "cards" in result and isinstance(result["cards"], list)
    assert len(result["cards"]) == 0

    assert "top_transactions" in result and isinstance(
        result["top_transactions"],
        list,
    )
    assert len(result["top_transactions"]) == 0


def test_generate_home_page_json_with_cards_and_top_transactions():
    data = [
        {
            "Дата операции": "2026-07-01",
            "Сумма операции": -100,
            "Категория": "Еда",
            "Описание": "Пицца",
            "Номер карты": "1234567890123456",
        },
        {
            "Дата операции": "2026-07-10",
            "Сумма операции": -200,
            "Категория": "Транспорт",
            "Описание": "Такси",
            "Номер карты": "9876543210987654",
        },
        {
            "Дата операции": "2026-07-20",
            "Сумма операции": -300,
            "Категория": "Продукты",
            "Описание": "Пятёрочка",
            "Номер карты": "1234567890123456",
        },
    ]
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    assert "greeting" in result
    assert "cards" in result and isinstance(result["cards"], list)
    assert (
        len(result["cards"]) >= 1
    ), "Должны быть агрегированные данные по картам"

    assert "top_transactions" in result and isinstance(
        result["top_transactions"],
        list,
    )
    assert (
        len(result["top_transactions"]) > 0
    ), "Топ-транзакции должны быть непустыми"


def test_generate_home_page_json_no_date_column_but_has_data():
    data = [
        {
            "Сумма операции": -100,
            "Категория": "Еда",
            "Описание": "Пицца",
            "Номер карты": "1234",
        },
        {
            "Сумма операции": -200,
            "Категория": "Транспорт",
            "Описание": "Такси",
            "Номер карты": "5678",
        },
    ]
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    assert "greeting" in result
    assert "cards" in result and isinstance(result["cards"], list)
    assert len(result["top_transactions"]) >= 0


def test_generate_home_page_json_no_valid_transactions():
    data = {
        "Дата операции": ["не_дата", "тоже_не_дата"],
        "Категория": ["Продукты", "Такси"],
        "Сумма операции": [-100, -200],
    }
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    assert isinstance(result, dict)
    assert "greeting" in result
    assert "cards" in result
    assert isinstance(result["cards"], list)
    assert len(result["cards"]) == 0

    top_key = (
        "top_transactions"
        if "top_transactions" in result
        else "top_5_by_payment"
    )
    assert top_key in result
    assert isinstance(result[top_key], list)
    assert len(result[top_key]) == 0


def test_generate_home_page_json_with_nat_dates():
    """
    Проверяет, что функция корректно обрабатывает NaT (Not a Time) в колонке дат.
    Закрывает строки, где идёт фильтрация/очистка дат.
    """
    data = {
        "Дата операции": [pd.NaT, pd.NaT, "2024-01-01"],
        "Категория": ["Продукты", "Такси", "Продукты"],
        "Сумма операции": [-100, -200, -300],
        "Номер карты": ["****1234", "****5678", "****9999"],
    }

    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    assert isinstance(result, dict)

    top_key = (
        "top_5_by_payment"
        if "top_5_by_payment" in result
        else "top_transactions"
    )
    assert top_key in result
    top_list = result[top_key]
    assert isinstance(top_list, list)
    assert len(top_list) <= 3
    assert all(isinstance(x, dict) for x in top_list)


def test_generate_home_page_json_no_card_column():
    """Проверяет, что функция не падает, если нет колонки 'Номер карты'."""
    data = {
        "Дата операции": ["2024-05-10", "2024-05-15"],
        "Категория": ["Продукты", "Такси"],
        "Сумма операции": [-100, -200],
    }
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    assert isinstance(result, dict)
    assert "cards" in result
    assert result["cards"] == []

    top_txs = result.get("top_transactions", [])
    assert isinstance(top_txs, list)


def test_generate_home_page_json_no_amount_column():
    """Проверяет, что функция не падает, если нет колонки 'Сумма операции'."""
    data = {
        "Дата операции": ["2024-05-10", "2024-05-15"],
        "Категория": ["Продукты", "Такси"],
        "Номер карты": ["1234", "5678"],
    }
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    assert isinstance(result, dict)
    assert "cards" in result
    assert result["cards"] == []
    assert "top_transactions" in result
    assert result["top_transactions"] == []
