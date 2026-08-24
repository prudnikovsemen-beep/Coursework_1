from datetime import datetime
from typing import Any, Dict, List

import pandas as pd
import requests


def get_greeting(hour: int) -> str:
    if 6 <= hour < 12:
        return "Доброе утро"
    elif 12 <= hour < 18:
        return "Добрый день"
    elif 18 <= hour < 23:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def fetch_currency_rates(currencies: List[str]) -> List[Dict[str, Any]]:
    rates = []
    for curr in currencies:
        try:
            resp = requests.get(
                f"https://api.exchangerate.host/latest?base=RUB&symbols={curr}",
                timeout=5,
            )
            resp.raise_for_status()
            data = resp.json()
            rate = data.get("rates", {}).get(curr)
            if rate and float(rate) > 0:
                rates.append({"currency": curr, "rate": float(rate)})
            else:
                rates.append({"currency": curr, "rate": 1.0})
        except Exception:
            rates.append({"currency": curr, "rate": 1.0})
    return rates


def fetch_stock_prices(stocks: List[str]) -> List[Dict[str, Any]]:
    mock_prices = {
        "AAPL": 150.12,
        "AMZN": 3173.18,
        "GOOGL": 2742.39,
        "MSFT": 296.71,
        "TSLA": 1007.08,
    }
    prices = []
    for s in stocks:
        p = mock_prices.get(s, 0.0)
        if p > 0:
            prices.append({"stock": s, "price": float(p)})
        else:
            prices.append({"stock": s, "price": 1.0})
    return prices


def generate_home_page_json(
    date_str: str,
    df: pd.DataFrame,
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    # Защита: если нет колонки или DataFrame пустой — сразу безопасный ответ
    if df.empty or "Дата операции" not in df.columns:
        now = datetime.now()
        return {
            "greeting": get_greeting(now.hour),
            "cards": [],
            "top_transactions": [],
            "currency_rates": fetch_currency_rates(settings.get("user_currencies", [])),
            "stock_prices": fetch_stock_prices(settings.get("user_stocks", [])),
        }

    # Делаем копию, чтобы не менять оригинал, и конвертируем даты: мусор станет NaT
    df = df.copy()
    df["Дата операции"] = pd.to_datetime(df["Дата операции"], errors="coerce")

    dt_range = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    start_of_month = dt_range.replace(day=1, hour=0, minute=0, second=0)

    now = datetime.now()
    greeting = get_greeting(now.hour)

    mask = (df["Дата операции"] >= start_of_month) & (df["Дата операции"] <= dt_range)
    filtered = df.loc[mask].copy()

    cards_data: List[Dict[str, Any]] = []
    if "Номер карты" in filtered.columns and not filtered.empty:
        grouped = filtered.groupby("Номер карты", dropna=True)["Сумма операции"].sum()
        for card_last4, total_spent in grouped.items():
            cashback = total_spent / 100.0
            last_digits = str(card_last4).strip()[-4:].zfill(4)
            cards_data.append(
                {
                    "last_digits": last_digits,
                    "total_spent": round(float(total_spent), 2),
                    "cashback": round(float(cashback), 2),
                }
            )

    top_transactions: List[Dict[str, Any]] = []
    if not filtered.empty and "Сумма операции" in filtered.columns:
        top5 = filtered.nlargest(5, "Сумма операции")
        for _, row in top5.iterrows():
            #  Обязательно добавь проверку на NaT, иначе strftime упадёт
            date_val = row["Дата операции"]
            if pd.isna(date_val):
                date_str_out = "Неизвестна"
            else:
                date_str_out = date_val.strftime("%d.%m.%Y")

            top_transactions.append(
                {
                    "date": date_str_out,
                    "amount": round(float(row["Сумма операции"]), 2),
                    "category": str(row.get("Категория", "")),
                    "description": str(row.get("Описание", "")),
                }
            )

    currency_rates = fetch_currency_rates(settings.get("user_currencies", []))
    stock_prices = fetch_stock_prices(settings.get("user_stocks", []))

    return {
        "greeting": greeting,
        "cards": cards_data,
        "top_transactions": top_transactions,
        "currency_rates": currency_rates,
        "stock_prices": stock_prices,
    }
