import tempfile
from unittest.mock import patch
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import pytest

from src.reports import spending_by_category, investment_bank
# simple_search удалён, так как в этих тестах не используется


@patch("src.reports.Path.mkdir", side_effect=lambda *args, **kwargs: None)
@patch("src.reports.logger.exception")
def test_spending_by_category_real_save_in_temp_dir(mock_exception, mock_mkdir):
    """
    Тест с реальной записью файла во временную директорию.
    Покрывает строки декоратора report_saver, включая mkdir и to_csv.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        data = {
            "Дата операции": [datetime.now() - timedelta(days=10)],
            "Категория": ["Продукты"],
            "Сумма операции": [-100],
        }
        df = pd.DataFrame(data)

        with patch("src.reports.Path", side_effect=lambda x: Path(tmpdir) if x == "reports" else Path(x)):
            result = spending_by_category(df)

            assert not result.empty
            assert len(result) == 1

            expected_path = Path(tmpdir) / "report_spending_by_category.csv"
            assert expected_path.exists(), "Файл отчёта должен быть создан"

            saved_df = pd.read_csv(expected_path)
            assert saved_df.shape[0] == 1
            assert "Категория" in saved_df.columns
            assert "Сумма" in saved_df.columns

        mock_exception.assert_not_called()


@patch("src.reports.Path.mkdir")
@patch("pandas.DataFrame.to_csv")
def test_spending_by_category_success(mock_to_csv, mock_mkdir):
    """Базовый успешный сценарий: данные есть, файл сохраняется."""
    today = datetime.now()
    data = {
        "Дата операции": [
            today - timedelta(days=10),
            today - timedelta(days=20),
            today - timedelta(days=50),
        ],
        "Категория": ["Продукты", "Транспорт", "Продукты"],
        "Сумма операции": [-1000, -500, -2000],
    }
    df = pd.DataFrame(data)
    result = spending_by_category(df)

    assert len(result) == 2
    products_row = result[result["Категория"] == "Продукты"]
    assert products_row["Сумма"].iloc[0] == -3000.0
    assert mock_to_csv.called
    assert mock_mkdir.called


def test_spending_by_category_empty_df():
    """Пустой DataFrame: функция возвращает пустой DF и логирует предупреждение."""
    df = pd.DataFrame()
    with patch("src.reports.logger.warning") as mock_warning:
        result = spending_by_category(df)

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    mock_warning.assert_called_once()
    assert "Отчёт пуст" in mock_warning.call_args[0][0]


@patch("src.reports.logger.warning")
def test_spending_by_category_filtered_empty(mock_warning):
    """Фильтрация дала пустой результат (транзакции есть, но не попадают в диапазон)."""
    data = {
        "Дата операции": [pd.Timestamp("2020-01-01")],
        "Категория": ["Продукты"],
        "Сумма операции": [-100]
    }
    df = pd.DataFrame(data)
    result = spending_by_category(df, date="2024-01-01")

    assert isinstance(result, pd.DataFrame)
    assert result.empty

    messages = [call[0][0] for call in mock_warning.call_args_list]
    assert any("Нет транзакций за последние 90 дней" in msg for msg in messages)


def test_spending_by_category_missing_critical_columns():
    """Отсутствие обязательных колонок вызывает ValueError."""
    df = pd.DataFrame({"Другое": [1, 2, 3]})
    with pytest.raises(ValueError) as exc_info:
        spending_by_category(df)

    error_msg = str(exc_info.value)
    assert "Дата операции" in error_msg
    assert "Категория" in error_msg
    assert "Сумма операции" in error_msg


def test_spending_by_category_invalid_date_format():
    """Некорректный формат даты вызывает ValueError."""
    data = {
        "Дата операции": [pd.Timestamp.now()],
        "Категория": ["Продукты"],
        "Сумма операции": [-100]
    }
    df = pd.DataFrame(data)
    with pytest.raises(ValueError):
        spending_by_category(df, date="не_дата")


@patch("src.reports.Path.mkdir")
@patch("pandas.DataFrame.to_csv")
@patch("src.reports.logger.exception")
def test_spending_by_category_save_exception_full_lifecycle(mock_exception, mock_to_csv, mock_mkdir):
    """Ошибка сохранения файла: функция возвращает DF, логирует ошибку, но не падает."""
    today = datetime.now()
    data = {
        "Дата операции": [today - timedelta(days=10)],
        "Категория": ["Продукты"],
        "Сумма операции": [-100],
    }
    df = pd.DataFrame(data)

    mock_to_csv.side_effect = OSError("Не удалось сохранить файл")
    result = spending_by_category(df)

    assert not result.empty, "Функция должна вернуть DataFrame даже при ошибке сохранения"
    assert mock_mkdir.called
    assert mock_to_csv.called
    assert mock_exception.called
    assert mock_exception.call_count == 1


@patch("src.reports.logger.warning")
def test_spending_by_category_mixed_dates(mock_warning):
    """Смешанные форматы дат: функция должна обработать и вернуть частичный результат."""
    data = {
        "Дата операции": ["2024-05-01", "не_дата", pd.NaT, "2024-05-10"],
        "Категория": ["Продукты", "Такси", "Продукты", "Транспорт"],
        "Сумма операции": [-100, -200, -300, -400],
    }
    df = pd.DataFrame(data)
    ref_date = datetime(2024, 5, 31, 12, 0, 0)
    result = spending_by_category(df, date=ref_date.strftime("%Y-%m-%d"))

    assert isinstance(result, pd.DataFrame)
    assert 0 <= result.shape[0] <= 2


@patch("src.reports.logger.warning")
def test_spending_by_category_all_dates_invalid(mock_warning):
    """Все даты невалидны: результат пустой, есть предупреждение."""
    data = {
        "Дата операции": ["не_дата_1", "не_дата_2", "не_дата_3"],
        "Категория": ["Продукты", "Такси", "Продукты"],
        "Сумма операции": [-100, -200, -150],
    }
    df = pd.DataFrame(data)
    result = spending_by_category(df)

    assert isinstance(result, pd.DataFrame)
    assert result.empty

    messages = [call[0][0] for call in mock_warning.call_args_list]
    assert any("Отчёт пуст" in msg or "Нет транзакций" in msg for msg in messages)


@patch("src.reports.Path.mkdir")
@patch("pandas.DataFrame.to_csv")
@patch("src.reports.logger.exception")
def test_report_saver_catches_to_csv_exception(mock_exception, mock_to_csv, mock_mkdir):
    """Декоратор ловит OSError и логирует через exception."""
    today = datetime.now()
    data = {
        "Дата операции": [today - timedelta(days=10)],
        "Категория": ["Продукты"],
        "Сумма операции": [-100],
    }
    df = pd.DataFrame(data)

    mock_to_csv.side_effect = OSError("Не удалось сохранить файл")
    result = spending_by_category(df)

    assert not result.empty
    assert mock_mkdir.called
    assert mock_to_csv.called
    assert mock_exception.called
    assert mock_exception.call_count == 1


@patch("src.reports.logger.warning")
def test_spending_by_category_no_transactions_in_last_90_days(mock_warning):
    """Транзакции есть, но все старше 90 дней: результат пустой, предупреждение есть."""
    data = {
        "Дата операции": ["2020-01-01", "2021-05-10", "2019-12-31"],
        "Категория": ["Продукты", "Такси", "Продукты"],
        "Сумма операции": [-100, -200, -150],
    }
    df = pd.DataFrame(data)
    df["Дата операции"] = pd.to_datetime(df["Дата операции"])

    result = spending_by_category(df)
    assert isinstance(result, pd.DataFrame)
    assert result.empty

    messages = [call[0][0] for call in mock_warning.call_args_list]
    assert any("Нет транзакций за последние 90 дней" in msg for msg in messages), \
        f"Ожидалось предупреждение о пустом диапазоне, но были: {messages}"


@patch("src.reports.Path.mkdir")
@patch("pandas.DataFrame.to_csv")
@patch("src.reports.logger.warning")
def test_spending_by_category_empty_result_no_save(mock_warning, mock_to_csv, mock_mkdir):
    """Когда результат пустой, файл не должен сохраняться."""
    data = {
        "Дата операции": [datetime.now() - timedelta(days=200)],  # вне диапазона 90 дней
        "Категория": ["Продукты"],
        "Сумма операции": [-100],
    }
    df = pd.DataFrame(data)

    result = spending_by_category(df)

    assert isinstance(result, pd.DataFrame)
    assert result.empty
    mock_to_csv.assert_not_called()  # Ключевое: файл не пишется

    messages = [call[0][0] for call in mock_warning.call_args_list]
    assert any("Отчёт пуст" in msg or "Нет транзакций" in msg for msg in messages)


# ТЕСТЫ ДЛЯ investment_bank

def test_investment_bank_basic_calculation():
    """Проверка базовой логики investment_bank: расчёт накоплений по порогу."""
    data = {
        "Дата операции": ["2024-05-01", "2024-05-15", "2024-06-01"],
        "Категория": ["Продукты", "Такси", "Продукты"],
        "Сумма операции": [-123, -87, -250],  # отрицательные траты
    }
    df = pd.DataFrame(data)
    # Считаем для мая 2024 с порогом 100
    result = investment_bank("2024-05", df, threshold=100)

    # В мае две траты: 123 и 87
    # 123: остаток 23 -> копим 100 - 23 = 77
    # 87: остаток 87 -> копим 100 - 87 = 13
    # Итого: 77 + 13 = 90
    assert result == 90.0


def test_investment_bank_no_data_returns_zero():
    """Если нет данных или колонка отсутствует — возвращается 0.0."""
    df = pd.DataFrame()
    result = investment_bank("2024-05", df, threshold=100)
    assert result == 0.0

    df_no_col = pd.DataFrame({"Категория": ["Продукты"]})
    result = investment_bank("2024-05", df_no_col, threshold=100)
    assert result == 0.0


def test_investment_bank_invalid_threshold():
    """Невалидный порог (0 или отрицательный) — возвращается 0.0 и предупреждение."""
    data = {
        "Дата операции": ["2024-05-01"],
        "Категория": ["Продукты"],
        "Сумма операции": [-100],
    }
    df = pd.DataFrame(data)

    with patch("src.reports.logger.warning") as mock_warning:
        result = investment_bank("2024-05", df, threshold=-10)
        assert result == 0.0
        mock_warning.assert_called()
        assert "Invalid threshold value" in mock_warning.call_args[0][0]
