from pathlib import PurePosixPath

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

        # Нормализуем пути и проверяем точное совпадение или совпадение по имени файла
        actual_names = {PurePosixPath(f).name: f for f in actual_files}
        actual_set = set(actual_files)

        present = []
        missing = []
        for expected in expected_files:
            if expected in actual_set:
                # Точное совпадение пути
                present.append(expected)
            elif PurePosixPath(expected).name in actual_names:
                # Файл есть, но в другой директории
                present.append(actual_names[PurePosixPath(expected).name])
            else:
                missing.append(expected)

        present_set = set(present)
        return {
            "present": present,
            "missing": missing,
            "extra_files": [f for f in actual_files if f not in present_set],
            "total_expected": len(expected_files),
            "total_found": len(present),
        }

    return check_artifacts
