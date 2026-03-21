import logging

from judge.settings import settings

logger = logging.getLogger(__name__)


async def read_roster(github_username: str) -> dict | None:
    """Прочитать запись студента из вкладки roster."""
    if not settings.google_service_account_json:
        logger.warning("Google Sheets not configured")
        return None

    # TODO: aiogoogle implementation
    # 1. Авторизация через service account
    # 2. GET spreadsheets/{id}/values/roster
    # 3. Найти строку по github_username
    return None


async def read_rubrics(lab_id: int, role: str = "*") -> list[dict]:
    """Прочитать рубрики для лабы и роли."""
    if not settings.google_service_account_json:
        return []

    # TODO: aiogoogle implementation
    return []


async def read_deadline(lab_id: int, group_id: str) -> str | None:
    """Прочитать дедлайн для лабы и группы."""
    if not settings.google_service_account_json:
        return None

    # TODO: aiogoogle implementation
    return None


async def write_result_row(row: dict) -> None:
    """Записать строку результата в вкладку results."""
    if not settings.google_service_account_json:
        logger.warning("Google Sheets not configured, skipping write")
        return

    # TODO: aiogoogle implementation
    # 1. Авторизация через service account
    # 2. POST spreadsheets/{id}/values/results:append
