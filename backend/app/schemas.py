from pydantic import BaseModel, field_validator
from typing import Optional


class AnalyzeRequest(BaseModel):
    """Request to analyze a Jira project backlog."""
    jira_url: str
    pat: str
    project_key: str
    issue_types: list[str] = ["Story", "Epic"]
    max_issues: int = 200
    
    @field_validator('jira_url')
    @classmethod
    def validate_jira_url(cls, v: str) -> str:
        if not v.startswith("https://"):
            raise ValueError("Jira URL must start with 'https://'")
        return v
    
    @field_validator('project_key')
    @classmethod
    def validate_project_key(cls, v: str) -> str:
        if not (2 <= len(v) <= 10):
            raise ValueError("Project key must be 2-10 characters")
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError("Project key must be alphanumeric (with optional - or _)")
        return v
    
    @field_validator('max_issues')
    @classmethod
    def validate_max_issues(cls, v: int) -> int:
        if not (1 <= v <= 1000):
            raise ValueError("max_issues must be between 1 and 1000")
        return v
    
    @field_validator('pat')
    @classmethod
    def validate_pat(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("PAT (Personal Access Token) must not be empty")
        return v


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
    ai_enabled: bool = False
