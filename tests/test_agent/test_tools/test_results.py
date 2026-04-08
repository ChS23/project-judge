from unittest.mock import AsyncMock, patch

import pytest

from judge.agent.tools.results import make_write_results
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


@patch("judge.agent.tools.results.write_result_row", new_callable=AsyncMock)
async def test_write_results_passes_all_fields(mock_write, pr):
    tool = make_write_results(pr)
    result = await tool.ainvoke(
        {
            "github_username": "student",
            "lab_id": 1,
            "deliverable_id": "D1",
            "criterion": "Конкретность",
            "score": 8.0,
            "max_score": 10.0,
            "penalty_coefficient": 0.9,
            "final_score": 7.2,
        }
    )

    mock_write.assert_called_once()
    row = mock_write.call_args[0][1]
    assert row["github_username"] == "student"
    assert row["deliverable_id"] == "D1"
    assert row["criterion"] == "Конкретность"
    assert row["score"] == 8.0
    assert row["max_score"] == 10.0
    assert row["penalty_coeff"] == 0.9
    assert row["final_score"] == 7.2
    assert row["pr_url"] == "https://github.com/org/repo/pull/1"
    assert "checked_at" in row
    assert "Записано" in result
