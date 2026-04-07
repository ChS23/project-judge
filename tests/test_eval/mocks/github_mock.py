"""Mock GitHub API client functions."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tests.test_eval.mocks import OutputCollector


def make_github_mocks(scenario, collector: OutputCollector):
    """Возвращает dict патчей для judge.github.client."""

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
        # Все строки валидны для inline comments
        return {p: set(range(1, 1000)) for p in scenario.files}

    return {
        "judge.github.client.get_pr_files": mock_get_pr_files,
        "judge.github.client.get_file_content": mock_get_file_content,
        "judge.github.client.post_comment": mock_post_comment,
        "judge.github.client.post_review": mock_post_review,
        "judge.github.client.add_label": mock_add_label,
        "judge.github.client.get_comments": mock_get_comments,
        "judge.github.client.get_pr_diff_lines": mock_get_pr_diff_lines,
    }
