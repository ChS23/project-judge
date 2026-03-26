import structlog
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import START, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from judge.github.client import get_comments, post_comment
from judge.llm.client import get_llm
from judge.models.pr import PRContext
from judge.tasks.broker import broker

logger = structlog.get_logger()

HINT_MARKER = "<!-- project-judge:hint -->"
MAX_HINTS = 5

ANSWER_PROMPT = """\
Ты — ассистент преподавателя курса "Системы ИИ".

Студент задал вопрос по своей оценке в PR. Твоя задача — НЕ давать готовый ответ, \
а направить студента в правильную сторону.

## Правила

- Не давай прямых ответов и готовых решений
- Задавай наводящие вопросы
- Указывай на конкретные разделы документации или спецификации где искать ответ
- Если вопрос про оценку — объясни по какому критерию снижен балл и что можно улучшить
- ВСЕГДА читай файлы студента перед ответом через `read_file` — не отвечай вслепую
- Если нужно — прочитай файл студента через `read_file` чтобы дать точную подсказку
- НЕ привязывайся к именам файлов — студент мог назвать файл иначе
- Если требуемая информация есть в файле с другим именем — это нормально
- Если студент сообщает что исправил замечания и просит перепроверить — \
вызови `trigger_recheck` и сообщи что перепроверка запущена
- Если вопрос не по теме — вежливо верни к делу
- Отвечай кратко, 2-4 предложения
- Отвечай на языке вопроса
- НЕ используй `post_comment` — ответ будет опубликован автоматически
"""


def _make_trigger_recheck(pr: PRContext):
    from langchain_core.tools import tool

    @tool
    async def trigger_recheck() -> str:
        """Запустить перепроверку PR.

        Вызывай когда студент явно или неявно просит перепроверить работу:
        - "Исправил, перепроверьте"
        - "Поправил замечания"
        - "Готово, можно проверять"
        - "Done, re-review please"
        - Любая формулировка означающая что студент внёс исправления и ждёт новой оценки
        """
        from judge.tasks.grade_pr import grade_pr

        await grade_pr.kiq(pr)
        return "Перепроверка запущена. Результат появится в PR через несколько минут."

    return trigger_recheck


def _build_qa_agent(pr: PRContext):
    from judge.agent.tools.artifacts import make_check_artifacts
    from judge.agent.tools.read_file import make_read_file
    from judge.agent.tools.spec import fetch_spec

    tools = [
        make_check_artifacts(pr),
        make_read_file(pr),
        fetch_spec,
        _make_trigger_recheck(pr),
    ]

    llm = get_llm()
    llm_with_tools = llm.bind_tools(tools)

    async def agent_node(state: MessagesState) -> dict:
        response = await llm_with_tools.ainvoke(state["messages"])
        return {"messages": [response]}

    graph = StateGraph(MessagesState)
    graph.add_node("agent", agent_node)
    graph.add_node("tools", ToolNode(tools))
    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()


def _count_hints(comments: list[dict]) -> int:
    return sum(1 for c in comments if HINT_MARKER in c["body"])


@broker.task
async def answer_question(
    pr_data: dict,
    question: str,
    comment_author: str,
) -> None:
    pr = PRContext.model_validate(pr_data)

    try:
        comments = await get_comments(pr)

        grading_comment = ""
        for c in reversed(comments):
            if c["user"].endswith("[bot]") and "Результат" in c["body"]:
                grading_comment = c["body"][:3000]
                break

        used = _count_hints(comments)
        hints_exhausted = used >= MAX_HINTS
        remaining = max(0, MAX_HINTS - used - 1)

        from judge.agent.graph import _langfuse_handler

        config = {}
        handler = _langfuse_handler()
        if handler:
            config["callbacks"] = [handler]
            config["run_name"] = f"qa-{pr.repo.split('/')[-1]}-{pr.pr_number}"
            config["metadata"] = {
                "repo": pr.repo,
                "pr_number": str(pr.pr_number),
                "author": comment_author,
                "type": "qa",
            }

        prompt = ANSWER_PROMPT
        if hints_exhausted:
            prompt += (
                "\n\n## Лимит подсказок исчерпан\n"
                "Студент исчерпал лимит подсказок. "
                "Если он просит перепроверку — вызови `trigger_recheck`. "
                "На вопросы отвечай кратко: лимит исчерпан, обратитесь к преподавателю."
            )

        messages = [SystemMessage(content=prompt)]
        if grading_comment:
            messages.append(
                HumanMessage(content=f"Предыдущая оценка бота:\n\n{grading_comment}")
            )
        messages.append(HumanMessage(content=question))

        agent = _build_qa_agent(pr)
        config["recursion_limit"] = 10
        result = await agent.ainvoke({"messages": messages}, config=config)

        reply = str(result["messages"][-1].content)

        # Если агент вызвал trigger_recheck — не считаем как хинт
        was_recheck = any(
            getattr(m, "name", None) == "trigger_recheck" for m in result["messages"]
        )

        if was_recheck:
            await post_comment(pr, reply)
            await logger.ainfo(
                "recheck_triggered_via_qa",
                pr=pr.pr_number,
                author=comment_author,
            )
        else:
            footer = (
                f"\n\n---\n"
                f"💡 *Подсказок осталось: {remaining}/{MAX_HINTS}*\n"
                f"{HINT_MARKER}"
            )
            await post_comment(pr, reply + footer)
            await logger.ainfo(
                "hint_sent",
                pr=pr.pr_number,
                author=comment_author,
                used=used + 1,
                remaining=remaining,
            )

    except Exception:
        await logger.aexception("answer_question_failed", pr=pr.pr_number)
