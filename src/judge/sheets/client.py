import json
import logging

from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds

from judge.settings import settings
from judge.sheets.cache import roster_cache, rubrics_cache

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def _get_creds() -> ServiceAccountCreds | None:
    if not settings.google_service_account_json:
        return None
    key = json.loads(settings.google_service_account_json)
    return ServiceAccountCreds(scopes=SCOPES, **key)


async def _get_values(range_: str) -> list[list[str]]:
    creds = _get_creds()
    if not creds:
        logger.warning("Google Sheets not configured")
        return []

    async with Aiogoogle(service_account_creds=creds) as ag:
        sheets = await ag.discover("sheets", "v4")
        resp = await ag.as_service_account(
            sheets.spreadsheets.values.get(
                spreadsheetId=settings.spreadsheet_id,
                range=range_,
            )
        )
    return resp.get("values", [])


async def _append_values(range_: str, values: list[list[str]]) -> None:
    creds = _get_creds()
    if not creds:
        logger.warning("Google Sheets not configured, skipping write")
        return

    async with Aiogoogle(service_account_creds=creds) as ag:
        sheets = await ag.discover("sheets", "v4")
        await ag.as_service_account(
            sheets.spreadsheets.values.append(
                spreadsheetId=settings.spreadsheet_id,
                range=range_,
                valueInputOption="USER_ENTERED",
                json={"values": values},
            )
        )


async def read_roster(github_username: str) -> dict | None:
    """Прочитать запись студента из вкладки roster."""
    cached = roster_cache.get(f"roster:{github_username}")
    if cached:
        return cached

    rows = await _get_values("roster!A:F")
    if not rows:
        return None

    # Header: github_username | full_name | group_id | team_name | role | topic
    header = rows[0]
    for row in rows[1:]:
        if len(row) > 0 and row[0] == github_username:
            record = dict(zip(header, row, strict=False))
            roster_cache.set(f"roster:{github_username}", record)
            return record

    return None


async def read_rubrics(lab_id: int, role: str = "*") -> list[dict]:
    """Прочитать рубрики для лабы и роли."""
    cache_key = f"rubrics:{lab_id}:{role}"
    cached = rubrics_cache.get(cache_key)
    if cached:
        return cached

    rows = await _get_values("rubrics!A:F")
    if not rows:
        return []

    # Header: lab_id | deliverable_id | role | criterion | max_score | weight
    header = rows[0]
    result = []
    for row in rows[1:]:
        record = dict(zip(header, row, strict=False))
        if str(record.get("lab_id")) != str(lab_id):
            continue
        row_role = record.get("role", "*")
        if role != "*" and row_role != "*" and row_role != role:
            continue
        result.append(record)

    rubrics_cache.set(cache_key, result)
    return result


async def read_deadline(lab_id: int, group_id: str) -> str | None:
    """Прочитать дедлайн для лабы и группы."""
    rows = await _get_values("deadlines!A:C")
    if not rows:
        return None

    # Header: lab_id | group_id | due_at
    for row in rows[1:]:
        if len(row) >= 3 and str(row[0]) == str(lab_id) and row[1] == group_id:
            return row[2]

    return None


async def write_result_row(row: dict) -> None:
    """Записать строку результата в вкладку results."""
    values = [
        [
            row.get("github_username", ""),
            str(row.get("lab_id", "")),
            row.get("deliverable_id", ""),
            row.get("criterion", ""),
            str(row.get("score", "")),
            str(row.get("max_score", "")),
            str(row.get("penalty_coeff", "")),
            str(row.get("final_score", "")),
            row.get("pr_url", ""),
            row.get("comment_url", ""),
            row.get("flags", ""),
            row.get("checked_at", ""),
        ]
    ]
    await _append_values("results!A:L", values)
