import structlog

from judge.agent.graph import run_agent
from judge.github.client import add_label
from judge.models.pr import PRContext
from judge.sheets.client import update_leaderboard
from judge.tasks.broker import broker

logger = structlog.get_logger()


@broker.task(retry_on_error=True, max_retries=1)
async def grade_pr(pr: PRContext) -> None:
    try:
        await logger.ainfo("grading_start", pr=pr.pr_number, sender=pr.sender)
        result = await run_agent(pr)
        await add_label(pr, "graded")
        await update_leaderboard(pr.repo)
        await logger.ainfo("grading_done", pr=pr.pr_number, result=result[:200])
    except Exception:
        await logger.aexception("grading_failed", pr=pr.pr_number)
        try:
            from judge.github.client import post_comment

            await post_comment(
                pr,
                "⚠️ Автопроверка завершилась с ошибкой. Преподаватель уведомлён.",
            )
            await add_label(pr, "grading-error")
        except Exception:
            await logger.aexception("error_notification_failed", pr=pr.pr_number)
        raise
