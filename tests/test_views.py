import pandas as pd
from datetime import datetime, timedelta
from src.views import generate_home_page_json


def test_generate_home_page_json_top_5_by_payment():
    data = {
        "Дата операции": ["2024-05-01", "2024-05-02", "2024-05-03", "2024-05-04", "2024-05-05"],
        "Сумма операции": [-100, -200, -300, -400, -500],
        "Категория": ["Продукты", "Продукты", "Транспорт", "Продукты", "Развлечения"],
        "Описание": ["Пятёрочка", "Магнит", "Такси", "Пятёрочка", "Кино"],
        "Номер карты": ["1234", "1234", "5678", "1234", "9999"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    settings = {"currency": "RUB"}
    result = generate_home_page_json("2024-05-31 12:00:00", df, settings)

    assert "top_transactions" in result
    assert len(result["top_transactions"]) == 5


def test_generate_home_page_json_empty_df():
    # Тест специально для покрытия веток, где DataFrame пустой
    df = pd.DataFrame()  # Пустой DataFrame
    settings = {"currency": "RUB"}

    result = generate_home_page_json("2024-05-31 12:00:00", df, settings)

    # Проверяем, что структура ответа всегда одинаковая
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
    # DataFrame не пустой, но колонки «Дата операции» нет
    data = [
        {"Сумма операции": 100, "Категория": "Еда", "Описание": "Пицца"},
    ]
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    # Функция должна безопасно вернуть ответ без транзакций
    assert "greeting" in result
    assert "cards" in result
    assert "top_transactions" in result
    assert isinstance(result["top_transactions"], list)
    assert len(result["top_transactions"]) == 0


def test_generate_home_page_json_all_dates_nan():
    data = [
        {"Дата операции": pd.NaT, "Сумма операции": -100, "Категория": "Еда", "Описание": "Пицца"},
        {"Дата операции": pd.NaT, "Сумма операции": -200, "Категория": "Транспорт", "Описание": "Такси"},
    ]
    df = pd.DataFrame(data)
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    assert "greeting" in result
    assert "top_transactions" in result
    # При всех NaT в датах фильтр ничего не найдёт
    assert isinstance(result["top_transactions"], list)
    assert len(result["top_transactions"]) == 0


def test_generate_home_page_json_empty_df_with_columns():
    # Пустой DataFrame с нужными колонками
    df = pd.DataFrame(columns=["Дата операции", "Сумма операции", "Категория"])
    date_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    settings = {"currency": "RUB"}

    result = generate_home_page_json(date_str, df, settings)

    assert isinstance(result, dict)

    # Проверяем, что структура ответа всегда одинаковая, даже если данных нет
    assert "greeting" in result
    assert "cards" in result
    assert isinstance(result["cards"], list)
    assert len(result["cards"]) == 0

    assert "top_transactions" in result
    assert isinstance(result["top_transactions"], list)
    assert len(result["top_transactions"]) == 0

    assert "currency_rates" in result
    assert "stock_prices" in result


def test_generate_home_page_json_full_flow_with_cards():
    data = {
        "Дата операции": [
            "2024-05-01", "2024-05-02", "2024-05-03", "2024-05-04", "2024-05-05",
            "2024-05-06", "2024-05-07", "2024-05-08", "2024-05-09", "2024-05-10",
        ],
        "Сумма операции": [-100, -200, -300, -400, -500, -600, -700, -800, -900, -1000],
        "Категория": ["Продукты"] * 10,
        "Описание": ["Покупка"] * 10,
        "Номер карты": ["1234", "1234", "5678", "5678", "9999", "1234", "5678", "9999", "1234", "5678"],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    date_str = "2024-05-31 12:00:00"
    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    assert "greeting" in result
    assert "cards" in result
    assert "top_transactions" in result

    # --- Проверка cards (группировка по картам) ---
    assert isinstance(result["cards"], list)
    assert len(result["cards"]) > 0

    cards_map = {c["last_digits"]: c for c in result["cards"]}

    # Карта 1234: -100 -200 -600 -900 = -1800
    assert "1234" in cards_map
    assert cards_map["1234"]["total_spent"] == -1800.0
    assert cards_map["1234"]["cashback"] == -18.0

    # Карта 5678: -300 -400 -700 -1000 = -2400
    assert "5678" in cards_map
    assert cards_map["5678"]["total_spent"] == -2400.0

    # Карта 9999: -500 -800 = -1300
    assert "9999" in cards_map
    assert cards_map["9999"]["total_spent"] == -1300.0

    # --- Проверка top_transactions ---
    # nlargest(5, "Сумма операции") для отрицательных чисел берёт «наибольшие» (т.е. ближе к 0)
    # Это: -100, -200, -300, -400, -500
    expected_amounts = [-100.0, -200.0, -300.0, -400.0, -500.0]

    amounts = [t["amount"] for t in result["top_transactions"]]
    assert amounts == expected_amounts


def test_generate_home_page_json_explicit_date_filter():
    """Явная проверка фильтрации по дате: только транзакции за последние 90 дней."""
    ref_date = datetime(2024, 5, 31, 12, 0, 0)
    date_str = ref_date.strftime("%Y-%m-%d %H:%M:%S")

    data = [
        # Старая транзакция: 60 дней назад → это апрель → НЕ должна попасть
        {"Дата операции": ref_date - timedelta(days=60), "Сумма операции": -100, "Категория": "Еда", "Описание": "Пицца", "Номер карты": "1234"},
        # Новая транзакция: 15 дней назад → середина мая → ДОЛЖНА попасть
        {"Дата операции": ref_date - timedelta(days=15), "Сумма операции": -200, "Категория": "Транспорт", "Описание": "Такси", "Номер карты": "5678"},
        # Ещё одна новая: 5 дней назад → конец мая → тоже должна попасть
        {"Дата операции": ref_date - timedelta(days=5), "Сумма операции": -300, "Категория": "Продукты", "Описание": "Магнит", "Номер карты": "9999"},
    ]
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    settings = {"user_currencies": [], "user_stocks": []}

    result = generate_home_page_json(date_str, df, settings)

    amounts = [t["amount"] for t in result["top_transactions"]]

    # Старая транзакция (-100) не должна быть в топе
    assert -100 not in amounts
    # Новые должны быть
    assert -200 in amounts
    assert -300 in amounts

    # Проверяем, что в картах тоже только новые транзакции
    cards_map = {c["last_digits"]: c for c in result["cards"]}
    assert "1234" not in cards_map  # старая карта
    assert "5678" in cards_map
    assert "9999" in cards_map
