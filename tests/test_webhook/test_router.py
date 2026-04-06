from unittest.mock import AsyncMock, patch

from gidgethub.sansio import Event

from judge.webhook.router import router


def _make_pr_event(action="opened"):
    return Event(
        data={
            "action": action,
            "number": 42,
            "repository": {"full_name": "org/repo"},
            "pull_request": {
                "user": {"login": "student"},
                "head": {"ref": "lab1", "sha": "abc123"},
                "html_url": "https://github.com/org/repo/pull/42",
                "body": "test PR",
                "created_at": "2026-01-01T00:00:00Z",
            },
            "installation": {"id": 1},
        },
        event="pull_request",
        delivery_id="test-123",
    )


@patch("judge.webhook.router.grade_pr")
async def test_pr_opened_enqueues_grade(mock_grade_pr):
    mock_grade_pr.kiq = AsyncMock()
    event = _make_pr_event("opened")
    await router.dispatch(event)
    mock_grade_pr.kiq.assert_called_once()


@patch("judge.webhook.router.grade_pr")
async def test_pr_synchronize_enqueues_grade(mock_grade_pr):
    mock_grade_pr.kiq = AsyncMock()
    event = _make_pr_event("synchronize")
    await router.dispatch(event)
    mock_grade_pr.kiq.assert_called_once()
