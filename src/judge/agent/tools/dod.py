import re

from langchain_core.tools import tool


@tool
def parse_dod(pr_body: str) -> dict:
    """Парсить DoD чеклист из описания PR. Считает выполненные и невыполненные пункты.

    Args:
        pr_body: Текст описания PR (markdown)
    """
    checked = len(re.findall(r"- \[x\]", pr_body, re.IGNORECASE))
    unchecked = len(re.findall(r"- \[ \]", pr_body))
    total = checked + unchecked

    return {
        "checked": checked,
        "unchecked": unchecked,
        "total": total,
        "completion_rate": round(checked / total, 2) if total > 0 else 0.0,
    }
