import structlog

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
- Если вопрос не по теме — вежливо верни к делу
- Отвечай кратко, 2-4 предложения
- Отвечай на языке вопроса

## Контекст

Репозиторий: {repo}
PR: #{pr_number}
Студент: @{sender}
"""


def _count_hints(comments: list[dict]) -> int:
    """Считает количество подсказок по скрытому HTML-маркеру."""
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
        used = _count_hints(comments)

        if used >= MAX_HINTS:
            await post_comment(
                pr,
                f"@{comment_author} Лимит подсказок ({MAX_HINTS}) исчерпан. "
                f"Для дальнейших вопросов обратитесь к преподавателю.",
            )
            return

        remaining = MAX_HINTS - used - 1

        llm = get_llm()
        prompt = ANSWER_PROMPT.format(
            repo=pr.repo,
            pr_number=pr.pr_number,
            sender=pr.sender,
        )

        response = await llm.ainvoke(
            [
                {"role": "system", "content": prompt},
                {"role": "user", "content": question},
            ]
        )

        reply = str(response.content)
        footer = (
            f"\n\n---\n💡 *Подсказок осталось: {remaining}/{MAX_HINTS}*\n{HINT_MARKER}"
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
