import structlog

from judge.agent.graph import run_agent
from judge.models.pr import PRContext
from judge.tasks.broker import broker

logger = structlog.get_logger()


@broker.task
async def grade_pr(pr: PRContext) -> None:
    await logger.ainfo("grading_start", pr=pr.pr_number, sender=pr.sender)
    result = await run_agent(pr)
    await logger.ainfo("grading_done", pr=pr.pr_number, result=result[:200])
