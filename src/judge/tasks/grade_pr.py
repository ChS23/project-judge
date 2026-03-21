import logging

from judge.agent.graph import run_agent
from judge.models.pr import PRContext
from judge.tasks.broker import broker

logger = logging.getLogger(__name__)


@broker.task
async def grade_pr(pr: PRContext) -> None:
    logger.info("Grading PR #%d from %s", pr.pr_number, pr.sender)
    result = await run_agent(pr)
    logger.info("Done grading PR #%d: %s", pr.pr_number, result[:100])
