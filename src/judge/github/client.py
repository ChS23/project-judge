import httpx
from gidgethub.httpx import GitHubAPI

from judge.github.auth import get_installation_token
from judge.models.pr import PRContext


async def _gh(pr: PRContext) -> GitHubAPI:
    token = await get_installation_token(pr.installation_id)
    return GitHubAPI(
        httpx.AsyncClient(),
        "project-judge",
        oauth_token=token,
    )


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


async def get_pr_files(pr: PRContext) -> list[str]:
    gh = await _gh(pr)
    files = []
    async for item in gh.getiter(f"/repos/{pr.repo}/pulls/{pr.pr_number}/files"):
        files.append(item["filename"])
    return files
