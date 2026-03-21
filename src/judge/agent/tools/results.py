from langchain_core.tools import tool


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
    # TODO: реализовать через sheets/client.py
    return f"Результаты записаны для {github_username}, lab {lab_id}"
