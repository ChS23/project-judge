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
    pr = PRContext(
        repo=data["repository"]["full_name"],
        pr_number=issue["number"],
        pr_url=issue["html_url"],
        sender=author,
        branch="",
        head_sha="",
        body=issue.get("body") or "",
        created_at=issue["created_at"],
        installation_id=data["installation"]["id"],
    )

    await logger.ainfo(
        "question_received",
        pr=pr.pr_number,
        author=author,
        question=body[:100],
    )
    await answer_question.kiq(pr.model_dump(), body, author)
