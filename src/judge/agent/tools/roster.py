from langchain_core.tools import tool

from judge.sheets.client import read_roster as _read_roster


@tool
async def read_roster(github_username: str) -> dict:
    """Найти студента по GitHub username. Возвращает группу, команду, роль и тему.

    Args:
        github_username: GitHub username студента
    """
    record = await _read_roster(github_username)
    if record is None:
        return {
            "github_username": github_username,
            "error": "Student not found in roster",
        }
    return record
