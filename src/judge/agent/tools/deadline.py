from datetime import datetime

from langchain_core.tools import tool


@tool
def check_deadline(pr_created_at: str, deadline: str) -> dict:
    """Рассчитать штраф за просрочку по дате открытия PR и дедлайну.

    Args:
        pr_created_at: ISO datetime когда PR был открыт
        deadline: ISO datetime дедлайна сдачи
    """
    created = datetime.fromisoformat(pr_created_at)
    due = datetime.fromisoformat(deadline)
    delta_days = (created - due).days

    if delta_days <= 0:
        coeff = 1.0
    elif delta_days <= 1:
        coeff = 0.9
    elif delta_days <= 3:
        coeff = 0.7
    elif delta_days <= 7:
        coeff = 0.5
    else:
        coeff = 0.2

    return {
        "days_late": max(0, delta_days),
        "coefficient": coeff,
        "on_time": delta_days <= 0,
    }
