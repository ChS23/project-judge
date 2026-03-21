from langchain_core.tools import tool

from judge.github.client import post_comment as _post_comment
from judge.models.pr import PRContext


@tool
async def post_comment(
    repo: str, pr_number: int, installation_id: int, body: str
) -> str:
    """Опубликовать комментарий в PR с результатами проверки.

    Args:
        repo: Полное имя репозитория (owner/repo)
        pr_number: Номер PR
        installation_id: ID инсталляции GitHub App
        body: Текст комментария в markdown
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
    await _post_comment(pr, body)
    return f"Комментарий опубликован в PR #{pr_number}"
