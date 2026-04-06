from unittest.mock import patch

import pytest

from judge.agent.tools.past_reviews import make_read_past_reviews
from judge.models.pr import PRContext


@pytest.fixture
def pr():
    return PRContext(
        repo="org/repo",
        pr_number=1,
        pr_url="https://github.com/org/repo/pull/1",
        sender="student",
        branch="lab1",
        head_sha="abc",
        body="",
        created_at="2026-01-01T00:00:00Z",
        installation_id=1,
    )


@patch("judge.agent.tools.past_reviews.get_comments")
async def test_no_past_reviews(mock_comments, pr):
    mock_comments.return_value = []
    tool = make_read_past_reviews(pr)
    result = await tool.ainvoke({})
    assert "первая проверка" in result.lower()


@patch("judge.agent.tools.past_reviews.get_comments")
async def test_with_past_reviews(mock_comments, pr):
    mock_comments.return_value = [
        {
            "user": "project-judge[bot]",
            "body": "## Результат автопроверки\n\nБалл: 80/100",
            "created_at": "2026-01-02T10:00:00Z",
        },
        {
            "user": "student",
            "body": "Исправил замечания",
            "created_at": "2026-01-02T11:00:00Z",
        },
    ]
    tool = make_read_past_reviews(pr)
    result = await tool.ainvoke({})
    assert "1 прошлых оценок" in result
    assert "80/100" in result


@patch("judge.agent.tools.past_reviews.get_comments")
async def test_ignores_non_bot_comments(mock_comments, pr):
    mock_comments.return_value = [
        {
            "user": "student",
            "body": "## Результат — мой собственный",
            "created_at": "2026-01-02T10:00:00Z",
        },
    ]
    tool = make_read_past_reviews(pr)
    result = await tool.ainvoke({})
    assert "первая проверка" in result.lower()
