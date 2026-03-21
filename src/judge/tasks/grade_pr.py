import logging

from judge.github.client import post_comment
from judge.models.pr import PRContext
from judge.tasks.broker import broker

logger = logging.getLogger(__name__)


@broker.task
async def grade_pr(pr: PRContext) -> None:
    logger.info("Grading PR #%d from %s", pr.pr_number, pr.sender)

    # TODO: запуск LangGraph графа
    # report = await build_graph().ainvoke({"pr": pr})

    await post_comment(pr, f"Received PR #{pr.pr_number}, grading...")
