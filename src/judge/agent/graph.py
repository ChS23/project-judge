import os
import re

import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langfuse.langchain import CallbackHandler
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from judge.agent.prompt import build_system_prompt
from judge.agent.tools import get_all_tools
from judge.llm.client import get_llm
from judge.models.pr import PRContext
from judge.settings import settings

logger = structlog.get_logger()

MAX_GRADING_ATTEMPTS = 2


def _langfuse_handler() -> CallbackHandler | None:
    if not settings.langfuse_public_key:
        return None
    os.environ.setdefault("LANGFUSE_PUBLIC_KEY", settings.langfuse_public_key)
    os.environ.setdefault("LANGFUSE_SECRET_KEY", settings.langfuse_secret_key)
    os.environ.setdefault("LANGFUSE_HOST", settings.langfuse_host)
    return CallbackHandler()


def build_agent(pr: PRContext):
    tools = get_all_tools(pr)
    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)
    system_prompt = build_system_prompt(pr)

    async def agent_node(state: MessagesState) -> dict:
        messages = [SystemMessage(content=system_prompt), *state["messages"]]
        response = await llm_with_tools.ainvoke(messages)
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()


def _validate_report(report: str, expected_criteria: int | None = None) -> list[str]:
    """Валидация отчёта агента. Возвращает список проблем (пустой = ок)."""
    issues = []

    # Проверяем наличие обязательных секций
    if "Результат автопроверки" not in report:
        issues.append("Отчёт не содержит секцию 'Результат автопроверки'")

    if "Итого" not in report and "итого" not in report.lower():
        issues.append("Отчёт не содержит итоговый балл")

    # Считаем строки таблицы оценок (| Критерий | Балл | ...)
    score_rows = re.findall(r"\|\s*[^|]+\s*\|\s*\d+\s*\|\s*\d+\s*\|", report)
    if expected_criteria and len(score_rows) < expected_criteria:
        issues.append(
            f"Оценено {len(score_rows)} критериев, ожидалось {expected_criteria}"
        )

    # Проверяем что есть хотя бы 1 оценённый критерий
    if not score_rows:
        issues.append("Нет ни одного оценённого критерия в таблице")

    return issues


async def run_agent(pr: PRContext) -> str:
    config = {}

    handler = _langfuse_handler()
    if handler:
        config["callbacks"] = [handler]

    config["run_name"] = f"grade-pr-{pr.repo.split('/')[-1]}-{pr.pr_number}"
    config["metadata"] = {
        "repo": pr.repo,
        "pr_number": str(pr.pr_number),
        "sender": pr.sender,
        "branch": pr.branch,
    }
    config["recursion_limit"] = 30

    last_report = ""
    for attempt in range(1, MAX_GRADING_ATTEMPTS + 1):
        agent = build_agent(pr)
        result = await agent.ainvoke(
            {"messages": [HumanMessage(content=f"Проверь PR #{pr.pr_number}")]},
            config=config,
        )
        last_report = str(result["messages"][-1].content)

        issues = _validate_report(last_report)
        if not issues:
            if attempt > 1:
                await logger.ainfo(
                    "grading_retry_succeeded",
                    pr=pr.pr_number,
                    attempt=attempt,
                )
            return last_report

        await logger.awarning(
            "grading_validation_failed",
            pr=pr.pr_number,
            attempt=attempt,
            issues=issues,
        )

    # Последняя попытка не прошла валидацию — возвращаем как есть
    await logger.awarning(
        "grading_validation_exhausted",
        pr=pr.pr_number,
        attempts=MAX_GRADING_ATTEMPTS,
    )
    return last_report
