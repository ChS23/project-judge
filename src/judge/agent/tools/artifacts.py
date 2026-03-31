from langchain_core.tools import tool

from judge.github.client import get_pr_files
from judge.models.pr import PRContext


def make_check_artifacts(pr: PRContext):
    @tool
    async def check_artifacts(expected_files: list[str]) -> dict:
        """Проверить наличие файлов в PR. Сравнивает файлы из diff с ожидаемым списком.

        Args:
            expected_files: Список ожидаемых файловых путей
        """
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

    return check_artifacts
