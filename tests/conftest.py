import os

import pytest

# Загрузить тестовые env vars до импорта settings
os.environ.setdefault("GITHUB_APP_ID", "0")
os.environ.setdefault("GITHUB_PRIVATE_KEY", "test")
os.environ.setdefault("GITHUB_WEBHOOK_SECRET", "test")
os.environ.setdefault("ZAI_API_KEY", "test")


@pytest.fixture
def sample_pr_payload():
    return {
        "action": "opened",
        "number": 42,
        "pull_request": {
            "html_url": "https://github.com/org/repo/pull/42",
            "user": {"login": "student1"},
            "head": {"ref": "lab2-mlops-deliverables", "sha": "abc123"},
            "body": "- [x] README\n- [ ] Architecture\n- [x] Tests",
            "created_at": "2026-03-20T23:47:00Z",
        },
        "repository": {"full_name": "org/repo"},
        "installation": {"id": 12345},
    }
