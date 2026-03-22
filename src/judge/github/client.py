import httpx
from gidgethub.httpx import GitHubAPI

from judge.github.auth import get_installation_token
from judge.models.pr import PRContext

_http_client: httpx.AsyncClient | None = None


async def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient()
    return _http_client


async def _gh(pr: PRContext) -> GitHubAPI:
    token = await get_installation_token(pr.installation_id)
    client = await _get_http_client()
    return GitHubAPI(client, "project-judge", oauth_token=token)


async def post_comment(pr: PRContext, body: str) -> None:
    gh = await _gh(pr)
    await gh.post(
        f"/repos/{pr.repo}/issues/{pr.pr_number}/comments",
        data={"body": body},
    )


async def add_label(pr: PRContext, label: str) -> None:
    gh = await _gh(pr)
    await gh.post(
        f"/repos/{pr.repo}/issues/{pr.pr_number}/labels",
        data={"labels": [label]},
    )


async def post_review(
    pr: PRContext,
    body: str,
    comments: list[dict],
    event: str = "COMMENT",
) -> None:
    """Создать PR review с inline-комментариями.

    Args:
        pr: Контекст PR
        body: Общий комментарий к review
        comments: Список dict с ключами path, line (или position), body
        event: COMMENT / REQUEST_CHANGES / APPROVE
    """
    gh = await _gh(pr)
    await gh.post(
        f"/repos/{pr.repo}/pulls/{pr.pr_number}/reviews",
        data={
            "commit_id": pr.head_sha,
            "body": body,
            "event": event,
            "comments": comments,
        },
    )


async def get_pr_files(pr: PRContext) -> list[str]:
    gh = await _gh(pr)
    files = []
    async for item in gh.getiter(f"/repos/{pr.repo}/pulls/{pr.pr_number}/files"):
        files.append(item["filename"])
    return files
