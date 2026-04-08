"""Mock E2B Sandbox for fast eval mode."""

import json
from unittest.mock import MagicMock


def make_sandbox_mock(scenario):
    """Возвращает патчи для sandbox: settings, auth token, e2b.Sandbox."""
    if not scenario.sandbox_report:
        return {}

    report_json = json.dumps(scenario.sandbox_report)

    def fake_sandbox_class(*args, **kwargs):
        sandbox = MagicMock()
        sandbox.git.clone = MagicMock()
        sandbox.commands.run = MagicMock(
            return_value=MagicMock(
                exit_code=0,
                stdout=report_json,
                stderr="",
            )
        )
        sandbox.files.read = MagicMock(return_value="mock file content")
        sandbox.kill = MagicMock()
        return sandbox

    async def fake_get_token(installation_id):
        return "fake-token-for-eval"

    mock_settings = MagicMock(e2b_api_key="fake-key", sandbox_timeout=600)

    return {
        # settings.e2b_api_key check
        "judge.agent.tools.sandbox.settings": mock_settings,
        # get_installation_token (JWT would fail with test key)
        "judge.agent.tools.sandbox.get_installation_token": fake_get_token,
        # e2b.Sandbox — lazy imported inside review_code
        "e2b.Sandbox": fake_sandbox_class,
    }
