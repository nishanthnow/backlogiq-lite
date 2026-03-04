import re
from ..schemas import JiraIssue, RuleFinding


def check_description_exists(issue: JiraIssue) -> RuleFinding:
    """
    Check if the issue has a meaningful description.
    Score: 10 if present and > 10 chars, 0 if empty/missing.
    """
    description = issue.description_text.strip() if issue.description_text else ""
    
    if len(description) > 10:
        score = 10.0
        finding = "Description is present and provides context."
        suggestion = "Continue to maintain detailed descriptions as issues evolve."
    else:
        score = 0.0
        finding = "Description is missing or too brief."
        suggestion = "Add a detailed description explaining the context, scope, and constraints. Include background on why this work matters to the team."
    
    return RuleFinding(
        rule_id="fast.description_exists",
        rule_name="Description Exists",
        score=score,
        max_score=10.0,
        severity="critical" if score < 4 else "moderate" if score < 8 else "info",
        finding=finding,
        suggestion=suggestion,
        field="description"
    )


def check_description_length(issue: JiraIssue) -> RuleFinding:
    """
    Check the character count of the description.
    Score: 0 if < 20 chars, linear scale up to 10 at 200+ chars.
    """
    description = issue.description_text.strip() if issue.description_text else ""
    length = len(description)
    
    if length < 20:
        score = 0.0
    elif length >= 200:
        score = 10.0
    else:
        # Linear scale from 0 to 10 between 20 and 200 chars
        score = (length - 20) / (200 - 20) * 10.0
    
    score = min(10.0, max(0.0, score))
    
    if length < 50:
        finding = f"Description is {length} characters — quite minimal."
        suggestion = "Expand the description to include user context, technical constraints, and business impact. Aim for 200+ characters."
    elif length < 200:
        finding = f"Description is {length} characters — a good start."
        suggestion = "Consider adding more detail about edge cases, acceptance criteria, or technical constraints."
    else:
        finding = f"Description is well-written at {length} characters."
        suggestion = "Great level of detail. Keep this standard for all future issues."
    
    return RuleFinding(
        rule_id="fast.description_length",
        rule_name="Description Length",
        score=score,
        max_score=10.0,
        severity="moderate" if score < 6 else "info",
        finding=finding,
        suggestion=suggestion,
        field="description"
    )


def check_acceptance_criteria_exist(issue: JiraIssue) -> RuleFinding:
    """
    Check if the issue has acceptance criteria defined.
    Score: 10 if found, 0 if not.
    """
    if issue.acceptance_criteria and issue.acceptance_criteria.strip():
        score = 10.0
        finding = "Acceptance criteria are clearly defined."
        suggestion = "Maintain this standard — well-defined criteria help prevent scope creep and provide clear done conditions."
    else:
        score = 0.0
        finding = "Acceptance criteria are missing."
        suggestion = "Add acceptance criteria using Given/When/Then format (BDD style) or as a checklist. Include at least 3 testable criteria. Example: 'Given a user on the dashboard, When they click Export, Then a CSV file downloads.'"
    
    return RuleFinding(
        rule_id="fast.acceptance_criteria_exist",
        rule_name="Acceptance Criteria",
        score=score,
        max_score=10.0,
        severity="critical" if score == 0 else "info",
        finding=finding,
        suggestion=suggestion,
        field="acceptance_criteria"
    )


def check_story_title_format(issue: JiraIssue) -> RuleFinding:
    """
    Check if the title follows the "As a X, I want Y, so that Z" format.
    Only applies to Stories.
    """
    # Skip for non-Stories
    if issue.issue_type.lower() not in ["story"]:
        return RuleFinding(
            rule_id="fast.story_title_format",
            rule_name="Story Title Format",
            score=10.0,
            max_score=10.0,
            severity="info",
            finding="N/A for this issue type",
            suggestion="N/A",
            field="summary"
        )
    
    # Check format: "As a [role], I want [goal], so that [benefit]"
    pattern = r"(?i)^as an?\s+.+,\s+i want\s+.+,\s+so that\s+.+"
    
    if re.match(pattern, issue.summary):
        score = 10.0
        finding = "Title follows the 'As a X, I want Y, so that Z' format."
        suggestion = "Excellent user story format. Keep this standard."
    elif issue.summary.lower().startswith("as a") or issue.summary.lower().startswith("as an"):
        score = 5.0
        finding = "Title starts with 'As a' but doesn't follow the full format."
        suggestion = "Complete the format: 'As a [role], I want [goal], so that [benefit]'. Ensure all three parts are clearly stated."
    else:
        score = 0.0
        finding = f"Title doesn't follow the user story format: '{issue.summary}'"
        suggestion = "Rewrite using the format: 'As a [role], I want [goal], so that [benefit]'. This clarifies the user perspective and value."
    
    return RuleFinding(
        rule_id="fast.story_title_format",
        rule_name="Story Title Format",
        score=score,
        max_score=10.0,
        severity="moderate" if score < 6 else "info",
        finding=finding,
        suggestion=suggestion,
        field="summary"
    )


def check_title_length(issue: JiraIssue) -> RuleFinding:
    """
    Check if the title is between 10 and 80 characters.
    Score varies by length.
    """
    length = len(issue.summary)
    
    if 10 <= length <= 80:
        score = 10.0
        finding = f"Title length is optimal at {length} characters."
        suggestion = "Great — this length is clear and specific."
    elif 80 < length <= 120:
        score = 7.0
        finding = f"Title is {length} characters — a bit long."
        suggestion = "Shorten to under 80 characters for better clarity. Break into multiple issues if needed."
    elif 5 <= length < 10:
        score = 5.0
        finding = f"Title is {length} characters — too brief."
        suggestion = "Add more context. Aim for 10-80 characters to provide clarity without being verbose."
    elif length > 120:
        score = 3.0
        finding = f"Title is {length} characters — way too long."
        suggestion = "Shorten significantly. Use 10-80 characters. Long titles often indicate scope creep — break into smaller stories."
    else:
        score = 0.0
        finding = f"Title is {length} characters — too short."
        suggestion = "Add more details. A good title should be 10+ characters and clearly describe the work."
    
    return RuleFinding(
        rule_id="fast.title_length",
        rule_name="Title Length",
        score=score,
        max_score=10.0,
        severity="info" if score >= 4 else "moderate",
        finding=finding,
        suggestion=suggestion,
        field="summary"
    )


def check_story_points_assigned(issue: JiraIssue) -> RuleFinding:
    """
    Check if the issue has story points assigned.
    Only applies to Stories.
    """
    # Skip for non-Stories
    if issue.issue_type.lower() not in ["story"]:
        return RuleFinding(
            rule_id="fast.story_points_assigned",
            rule_name="Story Points Assigned",
            score=10.0,
            max_score=10.0,
            severity="info",
            finding="N/A for this issue type",
            suggestion="N/A",
            field="story_points"
        )
    
    if issue.story_points is not None:
        score = 10.0
        finding = f"Story points assigned: {issue.story_points}"
        suggestion = "Good — this enables capacity planning and sprint forecasting."
    else:
        score = 0.0
        finding = "Story points are not assigned."
        suggestion = "Assign story points during refinement. This is essential for sprint capacity planning, team velocity tracking, and predictable delivery."
    
    return RuleFinding(
        rule_id="fast.story_points_assigned",
        rule_name="Story Points Assigned",
        score=score,
        max_score=10.0,
        severity="moderate" if score == 0 else "info",
        finding=finding,
        suggestion=suggestion,
        field="story_points"
    )


def check_not_oversized(issue: JiraIssue) -> RuleFinding:
    """
    Check if story points are not oversized (> 13).
    Only applies to Stories with story_points assigned.
    """
    # Skip for non-Stories
    if issue.issue_type.lower() not in ["story"]:
        return RuleFinding(
            rule_id="fast.not_oversized",
            rule_name="Not Oversized",
            score=10.0,
            max_score=10.0,
            severity="info",
            finding="N/A for this issue type",
            suggestion="N/A",
            field="story_points"
        )
    
    # Skip if no story points
    if issue.story_points is None:
        return RuleFinding(
            rule_id="fast.not_oversized",
            rule_name="Not Oversized",
            score=10.0,
            max_score=10.0,
            severity="info",
            finding="N/A — story points not assigned",
            suggestion="N/A",
            field="story_points"
        )
    
    points = issue.story_points
    
    if points <= 8:
        score = 10.0
        finding = f"Story is well-sized at {points} points."
        suggestion = "Excellent. This size is manageable and allows for focused, incremental delivery."
    elif points == 13:
        score = 5.0
        finding = f"Story is at the upper limit: {points} points."
        suggestion = "This is borderline. Consider if it can be decomposed into smaller, independently deliverable pieces. Stories larger than 13 points often hide scope."
    else:
        score = 0.0
        finding = f"Story is oversized at {points} points."
        suggestion = "Stories over 13 points should be decomposed into smaller, independently deliverable pieces. Large stories increase risk, hide bugs, and reduce velocity visibility."
    
    return RuleFinding(
        rule_id="fast.not_oversized",
        rule_name="Not Oversized",
        score=score,
        max_score=10.0,
        severity="critical" if points > 13 else "moderate" if points == 13 else "info",
        finding=finding,
        suggestion=suggestion,
        field="story_points"
    )
