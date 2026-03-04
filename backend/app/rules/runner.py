import asyncio
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
from .ai_rules import (
    ai_check_independence,
    ai_check_value_clarity,
    ai_check_testability,
)


async def run_all_rules(
    issue: JiraIssue,
    ai_enabled: bool = False,
    ai_client=None,
    ai_deployment: str = None,
    ai_semaphore: asyncio.Semaphore = None
) -> IssueAnalysis:
    """
    Run all quality check rules on an issue.
    
    Args:
        issue: The Jira issue to analyze
        ai_enabled: Whether to run AI rules (default False for now)
        ai_client: Azure OpenAI client (required if ai_enabled=True)
        ai_deployment: Azure OpenAI deployment name
        ai_semaphore: Semaphore to limit concurrent AI calls
    
    Returns:
        IssueAnalysis with all findings and an overall score
    """
    
    # Run fast rules (synchronous)
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
    
    # Run AI rules if enabled
    if ai_enabled and ai_client and ai_deployment:
        ai_rule_funcs = [ai_check_independence, ai_check_value_clarity, ai_check_testability]
        
        async def run_ai_rule(rule_func):
            if ai_semaphore:
                async with ai_semaphore:
                    return await rule_func(issue, ai_client, ai_deployment)
            else:
                return await rule_func(issue, ai_client, ai_deployment)
        
        try:
            ai_findings = await asyncio.gather(*[run_ai_rule(f) for f in ai_rule_funcs])
            findings.extend(ai_findings)
        except Exception as e:
            # If AI rules fail, continue with fast rules only
            print(f"Warning: AI rules failed for {issue.key}: {e}")
    
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
    
    # Determine overall severity
    if any(f.severity == "critical" for f in applicable_findings):
        severity = "critical"
    elif score < 70:
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
