from ..schemas import JiraIssue, IssueAnalysis
from .fast_rules import (
    check_description_exists,
    check_description_length,
    check_acceptance_criteria_exist,
    check_story_title_format,
    check_title_length,
    check_story_points_assigned,
    check_not_oversized,
)


async def run_all_rules(issue: JiraIssue) -> IssueAnalysis:
    """
    Run all fast quality check rules on an issue.
    
    Runs 7 fast sanity checks with instant execution (no AI, no external API calls).
    
    Args:
        issue: The Jira issue to analyze
    
    Returns:
        IssueAnalysis with all findings and an overall score (0-100)
    """
    
    # Run the 7 fast rules
    fast_rules = [
        check_description_exists,
        check_description_length,
        check_acceptance_criteria_exist,
        check_story_title_format,
        check_title_length,
        check_story_points_assigned,
        check_not_oversized,
    ]
    
    findings = [rule(issue) for rule in fast_rules]
    
    # Filter out N/A findings (not applicable to this issue type)
    applicable_findings = [f for f in findings if f.finding != "N/A for this issue type"]
    
    # Calculate weighted average score (0-100)
    if applicable_findings:
        total_score = sum(f.score for f in applicable_findings)
        total_max = sum(f.max_score for f in applicable_findings)
        score = (total_score / total_max) * 100 if total_max > 0 else 0.0
    else:
        score = 50.0  # Default if no applicable rules
    
    score = round(score, 1)
    
    # Determine overall severity based on score
    if score < 60:
        severity = "critical"
    elif score < 75:
        severity = "moderate"
    else:
        severity = "info"
    
    return IssueAnalysis(
        issue_key=issue.key,
        issue_url=issue.url,
        issue_type=issue.issue_type,
        issue_title=issue.summary,
        score=score,
        severity=severity,
        findings=applicable_findings
    )
