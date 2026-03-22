from unittest.mock import patch

import pytest

from judge.agent.tools.roster import make_read_roster
from judge.models.pr import PRContext


@pytest.fixture
def pr():
    return PRContext(
        repo="vstu-sii/bachelor-2025-team-test",
        pr_number=1,
        pr_url="https://github.com/org/repo/pull/1",
        sender="student",
        branch="lab1",
        head_sha="abc",
        body="",
        created_at="2026-01-01T00:00:00Z",
        installation_id=1,
    )


@patch("judge.agent.tools.roster._read_roster")
async def test_read_roster_found(mock_read, pr):
    mock_read.return_value = {
        "github_username": "ivanov-ii",
        "full_name": "Иванов Иван",
        "group_id": "ИВТ-1",
        "team_name": "Deep Logic",
        "role": "SA/PO",
        "topic": "Грейдер",
    }
    tool = make_read_roster(pr)
    result = await tool.ainvoke({"github_username": "ivanov-ii"})
    assert result["full_name"] == "Иванов Иван"
    assert result["role"] == "SA/PO"


@patch("judge.agent.tools.roster._read_roster")
async def test_read_roster_not_found(mock_read, pr):
    mock_read.return_value = None
    tool = make_read_roster(pr)
    result = await tool.ainvoke({"github_username": "unknown"})
    assert "error" in result
