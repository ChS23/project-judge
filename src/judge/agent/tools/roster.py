from langchain_core.tools import tool

from judge.models.pr import PRContext
from judge.sheets.client import read_roster as _read_roster


def make_read_roster(pr: PRContext):
    @tool
    async def read_roster(github_username: str) -> dict:
        """Найти студента по GitHub username. Возвращает группу, команду, роль и тему.

        Args:
            github_username: GitHub username студента
        """
        record = await _read_roster(pr.repo, github_username)
        if record is None:
            return {
                "github_username": github_username,
                "error": "Student not found in roster",
            }
        return record

    return read_roster
