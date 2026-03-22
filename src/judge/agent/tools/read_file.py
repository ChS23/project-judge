from langchain_core.tools import tool

from judge.github.client import get_file_content
from judge.models.pr import PRContext


def make_read_file(pr: PRContext):
    @tool
    async def read_file(path: str) -> str:
        """Прочитать содержимое файла из репозитория студента (ветка PR).

        Используй для чтения документов перед оценкой. Не привязывайся к именам
        файлов из спецификации — студент мог назвать файл иначе. Сначала посмотри
        какие файлы есть через check_artifacts, потом читай нужные.

        Args:
            path: Путь к файлу в репозитории (например docs/brief.md или README.md)
        """
        content = await get_file_content(pr, path)
        if content is None:
            return f"Файл {path} не найден или недоступен"
        if len(content) > 15000:
            return (
                content[:15000]
                + f"\n\n... (обрезано, полный размер: {len(content)} символов)"
            )
        return content

    return read_file
