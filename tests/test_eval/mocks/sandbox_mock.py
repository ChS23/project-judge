"""Mock E2B Sandbox for fast eval mode."""

import json
from unittest.mock import MagicMock


def make_sandbox_mock(scenario):
    """Возвращает патч для e2b.Sandbox, если сценарий имеет canned report."""
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

    return {"e2b.Sandbox": fake_sandbox_class}
