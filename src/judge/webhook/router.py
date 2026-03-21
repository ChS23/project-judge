import logging

from gidgethub.routing import Router
from gidgethub.sansio import Event

from judge.models.pr import PRContext
from judge.tasks.grade_pr import grade_pr

logger = logging.getLogger(__name__)

router = Router()


@router.register("pull_request", action="opened")
@router.register("pull_request", action="synchronize")
async def on_pull_request(event: Event) -> None:
    pr = PRContext.from_event(event.data)
    logger.info("PR #%d from %s on %s", pr.pr_number, pr.sender, pr.repo)
    await grade_pr.kiq(pr)
