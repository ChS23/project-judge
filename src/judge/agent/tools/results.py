from datetime import UTC, datetime

from langchain_core.tools import tool

from judge.models.pr import PRContext
from judge.sheets.client import write_result_row


def make_write_results(pr: PRContext):
    @tool
    async def write_results(
        github_username: str,
        lab_id: int,
        deliverable_id: str,
        criterion: str,
        score: float,
        max_score: float,
        penalty_coefficient: float,
        final_score: float,
        comment_url: str = "",
        flags: str = "",
    ) -> str:
        """Записать результат проверки одного критерия в Google Sheets.

        Вызывай отдельно для КАЖДОГО критерия. Например, если у deliverable D1
        три критерия — вызови write_results три раза.

        Args:
            github_username: GitHub username студента
            lab_id: Номер лабораторной
            deliverable_id: ID deliverable (например: D1, D2)
            criterion: Название критерия
            score: Балл за этот критерий
            max_score: Максимальный балл за критерий
            penalty_coefficient: Коэффициент штрафа (0.2 - 1.0)
            final_score: Итоговый балл = score * penalty_coefficient
            comment_url: URL опубликованного комментария
            flags: Флаги через запятую (needs-review, injection-detected)
        """
        await write_result_row(
            pr.repo,
            {
                "github_username": github_username,
                "lab_id": lab_id,
                "deliverable_id": deliverable_id,
                "criterion": criterion,
                "score": score,
                "max_score": max_score,
                "penalty_coeff": penalty_coefficient,
                "final_score": final_score,
                "pr_url": pr.pr_url,
                "comment_url": comment_url,
                "flags": flags,
                "checked_at": datetime.now(UTC).isoformat(),
            },
        )
        return f"Записано: {github_username}, lab {lab_id}, {deliverable_id}/{criterion}: {score}/{max_score}"

    return write_results
