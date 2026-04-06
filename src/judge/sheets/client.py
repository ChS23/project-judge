import json
from pathlib import Path

import structlog
from aiogoogle import Aiogoogle
from aiogoogle.auth.creds import ServiceAccountCreds

from judge.settings import settings
from judge.sheets.cache import roster_cache, rubrics_cache

logger = structlog.get_logger()

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


def resolve_spreadsheet_id(repo: str) -> str | None:
    """Определить spreadsheet_id по имени репозитория.

    Матчит repo name по префиксу из SPREADSHEET_MAP.
    Например: repo="vstu-sii/bachelor-2025-team-x" → prefix="bachelor-2025" → id.
    """
    if settings.spreadsheet_map:
        mapping = json.loads(settings.spreadsheet_map)
        repo_name = repo.split("/")[-1] if "/" in repo else repo
        for prefix, sid in mapping.items():
            if repo_name.startswith(prefix):
                return sid

    return settings.spreadsheet_id or None


# Маппинг русских заголовков → внутренние ключи
ROSTER_COLUMNS = {
    "GitHub Username": "github_username",
    "ФИО": "full_name",
    "Группа": "group_id",
    "Команда": "team_name",
    "Роль": "role",
    "Тема": "topic",
}

RUBRICS_COLUMNS = {
    "Лаба": "lab_id",
    "Deliverable": "deliverable_id",
    "Роль": "role",
    "Критерий": "criterion",
    "Макс. балл": "max_score",
    "Вес": "weight",
}

DEADLINES_COLUMNS = {
    "Лаба": "lab_id",
    "Группа": "group_id",
    "Дедлайн": "due_at",
}


def _get_creds() -> ServiceAccountCreds | None:
    sa = settings.google_service_account_json
    if not sa:
        return None

    key = json.loads(sa) if sa.startswith("{") else json.loads(Path(sa).read_text())

    return ServiceAccountCreds(scopes=SCOPES, **key)


def _normalize_row(header: list[str], row: list[str], column_map: dict) -> dict:
    """Превращает строку таблицы в dict с нормализованными ключами."""
    result = {}
    for i, col_name in enumerate(header):
        if i < len(row):
            key = column_map.get(col_name, col_name)
            result[key] = row[i]
    return result


async def _get_values(sid: str, range_: str) -> list[list[str]]:
    creds = _get_creds()
    if not creds:
        await logger.awarning("sheets_not_configured")
        return []

    async with Aiogoogle(service_account_creds=creds) as ag:
        sheets = await ag.discover("sheets", "v4")
        resp = await ag.as_service_account(
            sheets.spreadsheets.values.get(
                spreadsheetId=sid,
                range=range_,
            )
        )
    return resp.get("values", [])  # type: ignore[union-attr]


async def _append_values(sid: str, range_: str, values: list[list[str]]) -> None:
    creds = _get_creds()
    if not creds:
        await logger.awarning("sheets_not_configured", action="write_skipped")
        return

    async with Aiogoogle(service_account_creds=creds) as ag:
        sheets = await ag.discover("sheets", "v4")
        await ag.as_service_account(
            sheets.spreadsheets.values.append(
                spreadsheetId=sid,
                range=range_,
                valueInputOption="USER_ENTERED",
                json={"values": values},
            )
        )


async def read_roster(repo: str, github_username: str) -> dict | None:
    """Прочитать запись студента из вкладки roster."""
    cached = roster_cache.get(f"roster:{repo}:{github_username}")
    if cached:
        return cached

    sid = resolve_spreadsheet_id(repo)
    if not sid:
        await logger.awarning("no_spreadsheet_for_repo", repo=repo)
        return None

    rows = await _get_values(sid, "roster!A:F")
    if len(rows) < 2:
        return None

    header = rows[0]
    for row in rows[1:]:
        if not row or not row[0]:
            continue
        record = _normalize_row(header, row, ROSTER_COLUMNS)
        if record.get("github_username") == github_username:
            roster_cache.set(f"roster:{repo}:{github_username}", record)
            return record

    return None


async def read_rubrics(repo: str, lab_id: int, role: str = "*") -> list[dict]:
    """Прочитать рубрики для лабы и роли."""
    cache_key = f"rubrics:{repo}:{lab_id}:{role}"
    cached = rubrics_cache.get(cache_key)
    if cached:
        return cached

    sid = resolve_spreadsheet_id(repo)
    if not sid:
        return []

    rows = await _get_values(sid, "rubrics!A:F")
    if len(rows) < 2:
        return []

    header = rows[0]
    result = []
    for row in rows[1:]:
        if not row:
            continue
        record = _normalize_row(header, row, RUBRICS_COLUMNS)
        if str(record.get("lab_id")) != str(lab_id):
            continue
        row_role = record.get("role", "*")
        if role != "*" and row_role != "*" and row_role != role:
            continue
        result.append(record)

    rubrics_cache.set(cache_key, result)
    return result


async def read_deadline(repo: str, lab_id: int, group_id: str) -> str | None:
    """Прочитать дедлайн для лабы и группы."""
    sid = resolve_spreadsheet_id(repo)
    if not sid:
        return None

    rows = await _get_values(sid, "deadlines!A:C")
    if len(rows) < 2:
        return None

    header = rows[0]
    for row in rows[1:]:
        if not row:
            continue
        record = _normalize_row(header, row, DEADLINES_COLUMNS)
        if (
            str(record.get("lab_id")) == str(lab_id)
            and record.get("group_id") == group_id
        ):
            return record.get("due_at")

    return None


async def write_result_row(repo: str, row: dict) -> None:
    """Записать строку результата в вкладку results."""
    sid = resolve_spreadsheet_id(repo)
    if not sid:
        await logger.awarning(
            "no_spreadsheet_for_repo", repo=repo, action="write_skipped"
        )
        return

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
    await _append_values(sid, "results!A:L", values)


async def update_leaderboard(repo: str) -> None:
    """Пересчитать и обновить лидерборд команд.

    Читает results и roster, агрегирует лучший final_score
    каждого студента по каждой лабе, группирует по командам.
    Перезаписывает лист leaderboard.
    """
    sid = resolve_spreadsheet_id(repo)
    if not sid:
        await logger.awarning("leaderboard_skipped", repo=repo, reason="no spreadsheet")
        return

    # Читаем results и roster
    results_rows = await _get_values(sid, "results!A:L")
    roster_rows = await _get_values(sid, "roster!A:F")

    if len(results_rows) < 2 or len(roster_rows) < 2:
        return

    roster_header = roster_rows[0]

    # Маппинг username → team_name
    user_team: dict[str, str] = {}
    for row in roster_rows[1:]:
        if not row:
            continue
        record = _normalize_row(roster_header, row, ROSTER_COLUMNS)
        username = record.get("github_username", "")
        team = record.get("team_name", "")
        if username and team:
            user_team[username] = team

    # Собираем лучший final_score каждого студента по каждой лабе
    # Ключ: (username, lab_id) → лучший final_score
    best_scores: dict[tuple[str, str], float] = {}
    for row in results_rows[1:]:
        if not row:
            continue
        record = _normalize_row(roster_header, row, {})
        # results columns: username, lab_id, ..., final_score (idx 7)
        username = row[0] if len(row) > 0 else ""
        lab_id = row[1] if len(row) > 1 else ""
        try:
            score = float(row[7]) if len(row) > 7 and row[7] else 0.0
        except ValueError:
            score = 0.0

        key = (username, lab_id)
        if key not in best_scores or score > best_scores[key]:
            best_scores[key] = score

    # Агрегируем по командам
    # team → {total_score, member_count, labs}
    team_stats: dict[str, dict] = {}
    for (username, lab_id), score in best_scores.items():
        team = user_team.get(username, "")
        if not team:
            continue
        if team not in team_stats:
            team_stats[team] = {"total_score": 0.0, "members": set(), "labs": set()}
        team_stats[team]["total_score"] += score
        team_stats[team]["members"].add(username)
        team_stats[team]["labs"].add(lab_id)

    # Сортируем по total_score descending
    sorted_teams = sorted(
        team_stats.items(), key=lambda x: x[1]["total_score"], reverse=True
    )

    # Формируем таблицу
    header = ["#", "Команда", "Участники", "Лабы сдано", "Суммарный балл"]
    rows = [header]
    for rank, (team, stats) in enumerate(sorted_teams, 1):
        rows.append(
            [
                str(rank),
                team,
                str(len(stats["members"])),
                str(len(stats["labs"])),
                f"{stats['total_score']:.1f}",
            ]
        )

    # Перезаписываем лист leaderboard
    await _clear_and_write(sid, "leaderboard!A:E", rows)


async def _clear_and_write(sid: str, range_: str, values: list[list[str]]) -> None:
    """Очистить диапазон и записать новые данные."""
    creds = _get_creds()
    if not creds:
        return

    async with Aiogoogle(service_account_creds=creds) as ag:
        sheets = await ag.discover("sheets", "v4")
        # Очищаем
        await ag.as_service_account(
            sheets.spreadsheets.values.clear(
                spreadsheetId=sid,
                range=range_,
            )
        )
        # Пишем
        await ag.as_service_account(
            sheets.spreadsheets.values.update(
                spreadsheetId=sid,
                range=range_,
                valueInputOption="USER_ENTERED",
                json={"values": values},
            )
        )
