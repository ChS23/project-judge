import structlog
from gidgethub.routing import Router
from gidgethub.sansio import Event

from judge.models.pr import PRContext
from judge.tasks.answer_question import answer_question
from judge.tasks.grade_pr import grade_pr

logger = structlog.get_logger()

router = Router()


@router.register("pull_request", action="opened")
@router.register("pull_request", action="synchronize")
async def on_pull_request(event: Event) -> None:
    pr = PRContext.from_event(event.data)
    await logger.ainfo("pr_received", pr=pr.pr_number, sender=pr.sender, repo=pr.repo)
    await grade_pr.kiq(pr)
    await logger.ainfo("task_enqueued", pr=pr.pr_number)


@router.register("pull_request", action="labeled")
async def on_label(event: Event) -> None:
    label = event.data.get("label", {}).get("name", "")
    if label == "review-requested":
        pr = PRContext.from_event(event.data)
        await logger.ainfo("review_requested", pr=pr.pr_number, sender=pr.sender)


@router.register("issue_comment", action="created")
async def on_comment(event: Event) -> None:
    data = event.data

    if "pull_request" not in data.get("issue", {}):
        return

    comment = data["comment"]
    author = comment["user"]["login"]

    if author.endswith("[bot]"):
        return

    body = comment["body"].strip()
    if not body:
        return

    issue = data["issue"]

    # Получить head_sha из PR API (issue_comment не содержит PR details)
    from judge.github.auth import get_installation_token

    installation_id = data["installation"]["id"]
    token = await get_installation_token(installation_id)
    repo = data["repository"]["full_name"]

    import httpx

    async with httpx.AsyncClient() as client:
        pr_resp = await client.get(
            f"https://api.github.com/repos/{repo}/pulls/{issue['number']}",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
        )
        pr_data = pr_resp.json()

    pr = PRContext(
        repo=repo,
        pr_number=issue["number"],
        pr_url=issue["html_url"],
        sender=author,
        branch=pr_data.get("head", {}).get("ref", ""),
        head_sha=pr_data.get("head", {}).get("sha", ""),
        body=issue.get("body") or "",
        created_at=issue["created_at"],
        installation_id=installation_id,
    )

    await logger.ainfo(
        "question_received",
        pr=pr.pr_number,
        author=author,
        question=body[:100],
    )
    await answer_question.kiq(pr.model_dump(), body, author)
