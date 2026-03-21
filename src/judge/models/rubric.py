from pydantic import BaseModel


class RubricCriterion(BaseModel):
    lab_id: int
    deliverable_id: str
    role: str
    criterion: str
    max_score: float
    weight: float = 1.0


class LabSpec(BaseModel):
    lab_id: int
    url: str
    expected_files: list[str] = []
    dod_criteria: list[str] = []
