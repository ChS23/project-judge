import subprocess
import sys


def main() -> None:
    subprocess.run(  # noqa: S603
        [
            sys.executable,
            "-m",
            "granian",
            "judge.webhook.app:app",
            "--interface",
            "asgi",
            "--host",
            "0.0.0.0",  # noqa: S104
            "--port",
            "8000",
        ],
        check=True,
    )


if __name__ == "__main__":
    main()
