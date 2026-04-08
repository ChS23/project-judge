import re

import httpx
import structlog
from gidgethub.httpx import GitHubAPI

from judge.github.auth import get_installation_token
from judge.models.pr import PRContext

logger = structlog.get_logger()

_http_client: httpx.AsyncClient | None = None


async def _get_http_client() -> httpx.AsyncClient:
    global _http_client
    if _http_client is None or _http_client.is_closed:
        _http_client = httpx.AsyncClient()
    return _http_client


async def _gh(pr: PRContext) -> GitHubAPI:
    token = await get_installation_token(pr.installation_id)
    client = await _get_http_client()
    return GitHubAPI(client, "project-judge", oauth_token=token)


async def post_comment(pr: PRContext, body: str) -> None:
    gh = await _gh(pr)
    await gh.post(
        f"/repos/{pr.repo}/issues/{pr.pr_number}/comments",
        data={"body": body},
    )


async def add_label(pr: PRContext, label: str) -> None:
    gh = await _gh(pr)
    await gh.post(
        f"/repos/{pr.repo}/issues/{pr.pr_number}/labels",
        data={"labels": [label]},
    )


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)


async def get_pr_diff_lines(pr: PRContext) -> dict[str, set[int]]:
    """Получить множество строк в diff для каждого файла.

    Возвращает dict: {path: {line_numbers доступные для inline-комментариев}}.
    Только RIGHT-side строки (добавленные или контекст в новом файле).
    """
    gh = await _gh(pr)
    diff_lines: dict[str, set[int]] = {}

    async for file_data in gh.getiter(f"/repos/{pr.repo}/pulls/{pr.pr_number}/files"):
        path = file_data["filename"]
        patch = file_data.get("patch", "")
        if not patch:
            continue

        lines: set[int] = set()
        for match in _HUNK_RE.finditer(patch):
            start = int(match.group(1))
            _ = int(match.group(2)) if match.group(2) else 1
            # Парсим строки внутри hunk
            hunk_start = match.end()
            next_hunk = _HUNK_RE.search(patch, hunk_start)
            hunk_body = patch[
                hunk_start : next_hunk.start() if next_hunk else len(patch)
            ]

            line_num = start
            for raw_line in hunk_body.split("\n"):
                if raw_line.startswith("-"):
                    continue  # удалённая строка — нет в новом файле
                if raw_line.startswith("+") or not raw_line.startswith("\\"):
                    lines.add(line_num)
                    line_num += 1

        diff_lines[path] = lines

    return diff_lines


async def post_review(
    pr: PRContext,
    body: str,
    comments: list[dict],
    event: str = "COMMENT",
) -> None:
    """Создать PR review с inline-комментариями.

    Фильтрует комментарии — оставляет только те, чьи строки есть в diff.
    Если после фильтрации комментариев не осталось, постит обычный комментарий.
    """
    diff_lines = await get_pr_diff_lines(pr)

    valid_comments = []
    dropped = 0
    for c in comments:
        path = c.get("path", "")
        line = c.get("line", 0)
        if path in diff_lines and line in diff_lines[path]:
            valid_comments.append(
                {
                    "path": path,
                    "line": line,
                    "side": "RIGHT",
                    "body": c["body"],
                }
            )
        else:
            dropped += 1

    if dropped:
        await logger.ainfo(
            "review_comments_filtered",
            total=len(comments),
            valid=len(valid_comments),
            dropped=dropped,
        )

    gh = await _gh(pr)

    if valid_comments:
        await gh.post(
            f"/repos/{pr.repo}/pulls/{pr.pr_number}/reviews",
            data={
                "commit_id": pr.head_sha,
                "body": body,
                "event": event,
                "comments": valid_comments,
            },
        )
    elif body:
        # Нет валидных inline-комментариев — постим как обычный комментарий
        await post_comment(pr, body)


async def get_comments(pr: PRContext) -> list[dict]:
    """Получить комментарии PR."""
    gh = await _gh(pr)
    comments = []
    async for item in gh.getiter(f"/repos/{pr.repo}/issues/{pr.pr_number}/comments"):
        comments.append(
            {
                "user": item["user"]["login"],
                "body": item["body"],
                "created_at": item["created_at"],
            }
        )
    return comments


async def get_pr_files(pr: PRContext) -> list[str]:
    gh = await _gh(pr)
    files = []
    async for item in gh.getiter(f"/repos/{pr.repo}/pulls/{pr.pr_number}/files"):
        files.append(item["filename"])
    return files


async def get_file_content(pr: PRContext, path: str) -> str | None:
    """Прочитать содержимое файла из репозитория (ветка PR)."""
    gh = await _gh(pr)
    try:
        ref = pr.head_sha or pr.branch
        resp = await gh.getitem(
            f"/repos/{pr.repo}/contents/{path}?ref={ref}",
        )
        if resp.get("encoding") == "base64":
            import base64

            return base64.b64decode(resp["content"]).decode(errors="replace")
        return resp.get("content", "")
    except Exception:
        return None


async def get_pr_labels(pr: PRContext) -> list[str]:
    """Получить labels PR."""
    gh = await _gh(pr)
    labels = []
    async for item in gh.getiter(f"/repos/{pr.repo}/issues/{pr.pr_number}/labels"):
        labels.append(item["name"])
    return labels
