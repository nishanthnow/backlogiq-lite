from pydantic import BaseModel
from typing import Optional


class AnalyzeRequest(BaseModel):
    """Request to analyze a Jira project backlog."""
    jira_url: str
    pat: str
    project_key: str
    issue_types: list[str] = ["Story", "Epic"]
    max_issues: int = 200


class JiraIssue(BaseModel):
    """Normalized internal representation of a Jira issue."""
    key: str
    summary: str
    issue_type: str
    status: str
    description_text: str
    acceptance_criteria: Optional[str] = None
    story_points: Optional[float] = None
    labels: list[str] = []
    assignee: Optional[str] = None
    url: str


class RuleFinding(BaseModel):
    """Result of a single rule check."""
    rule_id: str
    rule_name: str
    score: float
    max_score: float = 10.0
    severity: str  # "critical" | "moderate" | "info"
    finding: str
    suggestion: str
    field: str


class IssueAnalysis(BaseModel):
    """Analysis results for a single issue."""
    issue_key: str
    issue_url: str
    issue_type: str
    issue_title: str
    score: float
    severity: str  # "critical" | "moderate" | "info"
    findings: list[RuleFinding]


class AnalysisReport(BaseModel):
    """Complete backlog analysis report."""
    overall_score: float
    total_issues: int
    severity_breakdown: dict[str, int]
    issues: list[IssueAnalysis]
    analyzed_at: str
