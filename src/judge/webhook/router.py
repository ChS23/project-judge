import structlog
from gidgethub.routing import Router
from gidgethub.sansio import Event

from judge.models.pr import PRContext
from judge.tasks.broker import broker
from judge.tasks.grade_pr import grade_pr

logger = structlog.get_logger()

router = Router()


@router.register("pull_request", action="opened")
@router.register("pull_request", action="synchronize")
async def on_pull_request(event: Event) -> None:
    pr = PRContext.from_event(event.data)
    await logger.ainfo("pr_received", pr=pr.pr_number, sender=pr.sender, repo=pr.repo)
    if not broker.is_worker_process:
        await broker.startup()
    await grade_pr.kiq(pr)
    await logger.ainfo("task_enqueued", pr=pr.pr_number)
