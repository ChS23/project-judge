from pydantic import BaseModel


class StudentRecord(BaseModel):
    github_username: str
    full_name: str = ""
    group_id: str = ""
    team_name: str = ""
    role: str = ""
    topic: str = ""
