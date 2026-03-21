from langchain_core.tools import tool

from judge.github.client import get_pr_files
from judge.models.pr import PRContext


@tool
async def check_artifacts(
    repo: str, pr_number: int, installation_id: int, expected_files: list[str]
) -> dict:
    """Проверить наличие файлов в PR. Сравнивает файлы из diff с ожидаемым списком.

    Args:
        repo: Полное имя репозитория (owner/repo)
        pr_number: Номер PR
        installation_id: ID инсталляции GitHub App
        expected_files: Список ожидаемых файловых путей
    """
    pr = PRContext(
        repo=repo,
        pr_number=pr_number,
        pr_url="",
        sender="",
        branch="",
        head_sha="",
        body="",
        created_at="2000-01-01T00:00:00Z",
        installation_id=installation_id,
    )
    actual_files = await get_pr_files(pr)

    present = [f for f in expected_files if any(f in a for a in actual_files)]
    missing = [f for f in expected_files if f not in present]

    return {
        "present": present,
        "missing": missing,
        "extra_files": [f for f in actual_files if f not in expected_files],
        "total_expected": len(expected_files),
        "total_found": len(present),
    }
