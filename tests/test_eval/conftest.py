from dotenv import load_dotenv

load_dotenv()


def pytest_configure(config):
    config.addinivalue_line("markers", "sandbox: tests using real E2B sandbox")
    config.addinivalue_line(
        "markers", "llm_eval: tests calling real LLM (slow, costs money)"
    )
