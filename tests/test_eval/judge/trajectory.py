"""Trajectory evaluation: проверяем что агент вызвал правильные tools."""

from __future__ import annotations

from langchain_core.messages import AIMessage


def extract_tool_calls(messages: list) -> list[str]:
    """Извлекает имена вызванных tools из messages."""
    tool_names = []
    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_names.append(tc["name"])
    return tool_names


def check_required_tools(
    messages: list,
    required: set[str],
) -> tuple[bool, set[str]]:
    """Проверяет что все required tools были вызваны.

    Returns:
        (passed, missing_tools)
    """
    called = set(extract_tool_calls(messages))
    missing = required - called
    return len(missing) == 0, missing


def check_forbidden_tools(
    messages: list,
    forbidden: set[str],
) -> tuple[bool, set[str]]:
    """Проверяет что forbidden tools НЕ были вызваны.

    Returns:
        (passed, called_forbidden)
    """
    called = set(extract_tool_calls(messages))
    found = forbidden & called
    return len(found) == 0, found


# Стандартные наборы для разных типов лаб
DOC_LAB_REQUIRED = {
    "read_past_reviews",
    "read_roster",
    "fetch_spec",
    "check_artifacts",
    "parse_dod",
    "check_deadline",
    "evaluate_content",
    "post_comment",
    "write_results",
}

DOC_LAB_FORBIDDEN = {
    "review_code",  # не должен вызывать sandbox для лаб с документами
}

CODE_LAB_REQUIRED = DOC_LAB_REQUIRED | {"review_code"}
CODE_LAB_FORBIDDEN: set[str] = set()
