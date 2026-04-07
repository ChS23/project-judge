import os
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from tests.test_eval.mocks import OutputCollector
from tests.test_eval.mocks.github_mock import make_github_mocks
from tests.test_eval.mocks.sandbox_mock import make_sandbox_mock
from tests.test_eval.mocks.sheets_mock import make_sheets_mocks

# Skip all eval tests if no real LLM API key
_skip_no_key = pytest.mark.skipif(
    not os.environ.get("ZAI_API_KEY") or os.environ.get("ZAI_API_KEY") == "test",
    reason="Eval tests require real ZAI_API_KEY",
)


def pytest_configure(config):
    config.addinivalue_line("markers", "sandbox: tests using real E2B sandbox")
    config.addinivalue_line(
        "markers", "llm_eval: tests calling real LLM (slow, costs money)"
    )


def _make_spec_httpx_mock(scenario):
    """Mock httpx in spec.py to return scenario's spec HTML."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.text = scenario.spec_html

    mock_client = AsyncMock()
    mock_client.get.return_value = mock_response
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    return {"judge.agent.tools.spec.httpx.AsyncClient": lambda *a, **kw: mock_client}


@pytest.fixture
def mock_externals(scenario):
    """Apply all external service mocks for a given scenario."""
    collector = OutputCollector()

    all_mocks = {
        **make_github_mocks(scenario, collector),
        **make_sheets_mocks(scenario, collector),
        **make_sandbox_mock(scenario),
        **_make_spec_httpx_mock(scenario),
    }

    with ExitStack() as stack:
        for target, mock_fn in all_mocks.items():
            stack.enter_context(patch(target, side_effect=mock_fn))
        yield collector
