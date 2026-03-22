from unittest.mock import patch

import pytest

from judge.agent.tools.artifacts import make_check_artifacts
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


@patch("judge.agent.tools.artifacts.get_pr_files")
async def test_check_artifacts_all_present(mock_files, pr):
    mock_files.return_value = ["README.md", "docs/use-cases.md", "docs/raci.md"]
    tool = make_check_artifacts(pr)
    result = await tool.ainvoke({"expected_files": ["README.md", "docs/use-cases.md"]})
    assert result["total_found"] == 2
    assert result["total_expected"] == 2
    assert len(result["missing"]) == 0


@patch("judge.agent.tools.artifacts.get_pr_files")
async def test_check_artifacts_some_missing(mock_files, pr):
    mock_files.return_value = ["README.md"]
    tool = make_check_artifacts(pr)
    result = await tool.ainvoke(
        {"expected_files": ["README.md", "docs/architecture.md"]}
    )
    assert result["total_found"] == 1
    assert "docs/architecture.md" in result["missing"]


@patch("judge.agent.tools.artifacts.get_pr_files")
async def test_check_artifacts_extra_files(mock_files, pr):
    mock_files.return_value = ["README.md", "extra.txt"]
    tool = make_check_artifacts(pr)
    result = await tool.ainvoke({"expected_files": ["README.md"]})
    assert "extra.txt" in result["extra_files"]
