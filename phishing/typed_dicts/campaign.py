from typing import TypedDict


class CampaignActivity(TypedDict):
    completed: int
    total: int


class DepartmentSecurityScoreRating(TypedDict):
    score: float
    high: float
    medium: float
    low: float


class DepartmentScore(TypedDict):
    security_score: DepartmentSecurityScoreRating
    risk_rating: DepartmentSecurityScoreRating
    department: str


class EmployeeScores(TypedDict):
    security_score: float | str
    risk_rating: float | str
