import json
import logging
from pathlib import Path
from typing import Any, Dict

from src.utils import load_transactions
from src.views import generate_home_page_json

# Раскомментируй, если будешь использовать сервисы в CLI
# from src.services import investment_bank, simple_search

logger = logging.getLogger(__name__)


def main() -> None:
    data_path = Path("data") / "operations.xlsx"
    settings_path = Path("user_settings.json")

    # Проверка наличия файлов (чтобы ошибки были понятными)
    if not data_path.exists():
        logger.error("Файл транзакций не найден: %s", data_path)
        return
    if not settings_path.exists():
        logger.error("Файл настроек не найден: %s", settings_path)
        return

    try:
        df = load_transactions(data_path)
        if df.empty:
            logger.warning("Загружен пустой DataFrame транзакций.")
    except Exception as e:
        logger.exception("Ошибка при загрузке транзакций: %s", e)
        return

    try:
        with open(settings_path, "r", encoding="utf-8") as f:
            settings: Dict[str, Any] = json.load(f)
    except json.JSONDecodeError as e:
        logger.exception("Ошибка парсинга user_settings.json: %s", e)
        return
    except Exception as e:
        logger.exception("Ошибка чтения user_settings.json: %s", e)
        return

    # Дата для генерации отчёта (можно вынести в аргументы CLI)
    reference_date = "2024-05-20 14:30:00"

    try:
        home_json = generate_home_page_json(reference_date, df, settings)
        # Для CLI-вывода можно оставить print, но лучше логировать факт генерации
        logger.info("JSON для главной страницы успешно сгенерирован")
        print(json.dumps(home_json, ensure_ascii=False, indent=2))
    except Exception as e:
        logger.exception("Ошибка при генерации JSON для главной страницы: %s", e)


if __name__ == "__main__":
    # Базовая настройка логгера для запуска без внешней конфигурации
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    )
    main()
