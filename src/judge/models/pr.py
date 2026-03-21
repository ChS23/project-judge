from datetime import datetime

from pydantic import BaseModel


class PRContext(BaseModel):
    """Контекст PR, извлечённый из webhook payload."""

    repo: str
    pr_number: int
    pr_url: str
    sender: str
    branch: str
    head_sha: str
    body: str
    created_at: datetime
    installation_id: int

    @classmethod
    def from_event(cls, data: dict) -> "PRContext":
        pr = data["pull_request"]
        return cls(
            repo=data["repository"]["full_name"],
            pr_number=data["number"],
            pr_url=pr["html_url"],
            sender=pr["user"]["login"],
            branch=pr["head"]["ref"],
            head_sha=pr["head"]["sha"],
            body=pr.get("body", ""),
            created_at=pr["created_at"],
            installation_id=data["installation"]["id"],
        )
