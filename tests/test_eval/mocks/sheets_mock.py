"""Mock Google Sheets client functions.

Patches at import sites (where functions are used), not at source.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.test_eval.mocks import OutputCollector


def make_sheets_mocks(scenario, collector: OutputCollector):
    """Возвращает dict патчей для Sheets client — по месту импорта."""

    async def mock_read_roster(repo, github_username):
        return scenario.roster_entry

    async def mock_read_rubrics(repo, lab_id, role="*"):
        return scenario.rubrics

    async def mock_read_deadline(repo, lab_id, group_id):
        return scenario.deadline

    async def mock_write_result_row(repo, row):
        collector.results.append(row)

    async def mock_update_leaderboard(repo):
        pass

    return {
        # Patch at import sites
        "judge.agent.tools.roster._read_roster": mock_read_roster,
        "judge.agent.tools.results.write_result_row": mock_write_result_row,
        "judge.tasks.grade_pr.update_leaderboard": mock_update_leaderboard,
        # Patch at source for any direct calls
        "judge.sheets.client.read_roster": mock_read_roster,
        "judge.sheets.client.read_rubrics": mock_read_rubrics,
        "judge.sheets.client.read_deadline": mock_read_deadline,
        "judge.sheets.client.write_result_row": mock_write_result_row,
        "judge.sheets.client.update_leaderboard": mock_update_leaderboard,
    }
