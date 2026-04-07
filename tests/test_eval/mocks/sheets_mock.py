"""Mock Google Sheets client functions."""

from tests.test_eval.mocks import OutputCollector


def make_sheets_mocks(scenario, collector: "OutputCollector"):
    """Возвращает dict патчей для judge.sheets.client."""

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
        "judge.sheets.client.read_roster": mock_read_roster,
        "judge.sheets.client.read_rubrics": mock_read_rubrics,
        "judge.sheets.client.read_deadline": mock_read_deadline,
        "judge.sheets.client.write_result_row": mock_write_result_row,
        "judge.sheets.client.update_leaderboard": mock_update_leaderboard,
    }
