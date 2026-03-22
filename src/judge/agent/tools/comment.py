from langchain_core.tools import tool

from judge.github.client import post_comment as _post_comment
from judge.models.pr import PRContext


def make_post_comment(pr: PRContext):
    @tool
    async def post_comment(body: str) -> str:
        """Опубликовать комментарий в PR с результатами проверки.

        Args:
            body: Текст комментария в markdown
        """
        await _post_comment(pr, body)
        return f"Комментарий опубликован в PR #{pr.pr_number}"

    return post_comment
