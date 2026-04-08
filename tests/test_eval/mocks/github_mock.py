"""Mock GitHub API client functions.

Patches at import sites (where functions are used), not at source.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.test_eval.mocks import OutputCollector


def make_github_mocks(scenario, collector: OutputCollector):
    """Возвращает dict патчей для GitHub client — по месту импорта."""

    async def mock_get_pr_files(pr):
        return list(scenario.files.keys())

    async def mock_get_file_content(pr, path):
        return scenario.files.get(path)

    async def mock_post_comment(pr, body):
        collector.comments.append(body)

    async def mock_post_review(pr, body, comments, event="COMMENT"):
        collector.reviews.append({"body": body, "comments": comments, "event": event})

    async def mock_add_label(pr, label):
        collector.labels.append(label)

    async def mock_get_comments(pr):
        return scenario.past_reviews

    async def mock_get_pr_diff_lines(pr):
        return {p: set(range(1, 1000)) for p in scenario.files}

    return {
        # Patch at import sites
        "judge.agent.tools.artifacts.get_pr_files": mock_get_pr_files,
        "judge.agent.tools.read_file.get_file_content": mock_get_file_content,
        "judge.agent.tools.comment._post_comment": mock_post_comment,
        "judge.agent.tools.comment._add_label": mock_add_label,
        "judge.agent.tools.past_reviews.get_comments": mock_get_comments,
        "judge.agent.tools.sandbox.post_review": mock_post_review,
        # These are called from client.py internally — patch there too
        "judge.github.client.get_pr_diff_lines": mock_get_pr_diff_lines,
        "judge.github.client.post_comment": mock_post_comment,
        "judge.github.client.add_label": mock_add_label,
    }
