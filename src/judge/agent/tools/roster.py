from langchain_core.tools import tool


@tool
async def read_roster(github_username: str) -> dict:
    """Найти студента по GitHub username. Возвращает группу, команду, роль и тему.

    Args:
        github_username: GitHub username студента
    """
    # TODO: реализовать через sheets/client.py
    return {
        "github_username": github_username,
        "full_name": "",
        "group_id": "",
        "team_name": "",
        "role": "",
        "topic": "",
        "error": "sheets client not implemented yet",
    }
