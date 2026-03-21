from datetime import UTC, datetime

from langchain_core.tools import tool

from judge.sheets.client import write_result_row


@tool
async def write_results(
    github_username: str,
    lab_id: int,
    scores: str,
    penalty_coefficient: float,
    final_score: float,
    pr_url: str,
    comment_url: str,
    flags: str = "",
) -> str:
    """Записать результаты проверки в Google Sheets.

    Args:
        github_username: GitHub username студента
        lab_id: Номер лабораторной
        scores: JSON строка с оценками по критериям
        penalty_coefficient: Коэффициент штрафа (0.2 - 1.0)
        final_score: Итоговый балл
        pr_url: URL проверенного PR
        comment_url: URL опубликованного комментария
        flags: Флаги через запятую (needs-review, injection-detected)
    """
    await write_result_row(
        {
            "github_username": github_username,
            "lab_id": lab_id,
            "score": scores,
            "penalty_coeff": penalty_coefficient,
            "final_score": final_score,
            "pr_url": pr_url,
            "comment_url": comment_url,
            "flags": flags,
            "checked_at": datetime.now(UTC).isoformat(),
        }
    )
    return f"Результаты записаны для {github_username}, lab {lab_id}"
