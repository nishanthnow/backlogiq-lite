import json
import logging
from typing import Optional
from openai import AsyncAzureOpenAI

from ..schemas import JiraIssue, RuleFinding

logger = logging.getLogger(__name__)


def get_ai_client(settings) -> AsyncAzureOpenAI:
    """Create an AsyncAzureOpenAI client from settings."""
    return AsyncAzureOpenAI(
        azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        api_key=settings.AZURE_OPENAI_API_KEY,
        api_version=settings.AZURE_OPENAI_API_VERSION,
    )


SYSTEM_PROMPT = """You are a senior Agile coach evaluating backlog quality for a consumer intelligence product team. 
Consumer intelligence involves: consumer behavior data, market research, survey data, audience segmentation, 
brand tracking, and retail analytics.

You evaluate individual Jira issues and provide specific, constructive feedback.
Your tone is supportive and educational — like a mentor, not an auditor.

Always respond in valid JSON with exactly these fields:
{
  "score": <number 0-10>,
  "finding": "<what you observed, 1-2 sentences>",
  "suggestion": "<specific improvement, 2-3 sentences>"
}
"""


async def ai_check_independence(
    issue: JiraIssue,
    client: AsyncAzureOpenAI,
    deployment: str
) -> RuleFinding:
    """
    Evaluate if the story is independently deliverable.
    """
    user_prompt = f"""Evaluate if this story is independently deliverable — can the team complete it 
without waiting on other stories or external blockers?

Title: {issue.summary}
Type: {issue.issue_type}
Description: {issue.description_text[:1000]}

Score 0-10 where:
- 10 = fully independent, no dependencies
- 5 = some implicit dependencies but manageable
- 0 = blocked or tightly coupled to other work

Respond in JSON only."""
    
    try:
        response = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            timeout=30.0
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
                data = json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
                data = json.loads(json_str)
            else:
                # Last resort: try to find JSON object
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    data = json.loads(response_text[start_idx:end_idx])
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
        
        return RuleFinding(
            rule_id="ai.independence",
            rule_name="Story Independence",
            score=float(data.get("score", 5)),
            max_score=10.0,
            severity="critical" if float(data.get("score", 5)) < 4 else "moderate" if float(data.get("score", 5)) < 7 else "info",
            finding=data.get("finding", "Unable to evaluate"),
            suggestion=data.get("suggestion", "Review dependencies before starting work"),
            field="description"
        )
    
    except Exception as e:
        logger.warning(f"AI evaluation failed for {issue.key}: {str(e)}")
        return RuleFinding(
            rule_id="ai.independence",
            rule_name="Story Independence",
            score=5.0,
            max_score=10.0,
            severity="info",
            finding="AI evaluation unavailable for this issue",
            suggestion="Please review the issue description manually for dependencies",
            field="description"
        )


async def ai_check_value_clarity(
    issue: JiraIssue,
    client: AsyncAzureOpenAI,
    deployment: str
) -> RuleFinding:
    """
    Evaluate if the business value is clearly communicated.
    """
    user_prompt = f"""Does this item clearly communicate the business value or user benefit? 
Would a stakeholder (brand manager, research director) understand WHY this matters?

Title: {issue.summary}
Type: {issue.issue_type}
Description: {issue.description_text[:1000]}

Score 0-10 where:
- 10 = clear value proposition linked to user outcomes
- 5 = some value implied but not explicit
- 0 = no discernible business value stated

Respond in JSON only."""
    
    try:
        response = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            timeout=30.0
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
                data = json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
                data = json.loads(json_str)
            else:
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    data = json.loads(response_text[start_idx:end_idx])
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
        
        return RuleFinding(
            rule_id="ai.value_clarity",
            rule_name="Value Clarity",
            score=float(data.get("score", 5)),
            max_score=10.0,
            severity="critical" if float(data.get("score", 5)) < 4 else "moderate" if float(data.get("score", 5)) < 7 else "info",
            finding=data.get("finding", "Unable to evaluate"),
            suggestion=data.get("suggestion", "Clarify the business value and user impact"),
            field="description"
        )
    
    except Exception as e:
        logger.warning(f"AI evaluation failed for {issue.key}: {str(e)}")
        return RuleFinding(
            rule_id="ai.value_clarity",
            rule_name="Value Clarity",
            score=5.0,
            max_score=10.0,
            severity="info",
            finding="AI evaluation unavailable for this issue",
            suggestion="Please review the issue description manually for clear business value",
            field="description"
        )


async def ai_check_testability(
    issue: JiraIssue,
    client: AsyncAzureOpenAI,
    deployment: str
) -> RuleFinding:
    """
    Evaluate if acceptance criteria enable independent testing.
    """
    user_prompt = f"""Are the acceptance criteria specific enough that a QA engineer could write 
test cases without asking questions? Are edge cases considered?

Title: {issue.summary}
Type: {issue.issue_type}
Description: {issue.description_text[:1000]}
Acceptance Criteria: {issue.acceptance_criteria or 'NONE PROVIDED'}

Score 0-10 where:
- 10 = clear, specific, independently verifiable criteria with edge cases
- 5 = some criteria but vague or incomplete
- 0 = no testable criteria at all

Respond in JSON only."""
    
    try:
        response = await client.chat.completions.create(
            model=deployment,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=500,
            timeout=30.0
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Try to extract JSON from response
        try:
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in response_text:
                json_str = response_text.split("```json")[1].split("```")[0]
                data = json.loads(json_str)
            elif "```" in response_text:
                json_str = response_text.split("```")[1].split("```")[0]
                data = json.loads(json_str)
            else:
                start_idx = response_text.find("{")
                end_idx = response_text.rfind("}") + 1
                if start_idx >= 0 and end_idx > start_idx:
                    data = json.loads(response_text[start_idx:end_idx])
                else:
                    raise json.JSONDecodeError("No JSON found", response_text, 0)
        
        return RuleFinding(
            rule_id="ai.testability",
            rule_name="Testability",
            score=float(data.get("score", 5)),
            max_score=10.0,
            severity="critical" if float(data.get("score", 5)) < 4 else "moderate" if float(data.get("score", 5)) < 7 else "info",
            finding=data.get("finding", "Unable to evaluate"),
            suggestion=data.get("suggestion", "Add more specific, testable acceptance criteria"),
            field="acceptance_criteria"
        )
    
    except Exception as e:
        logger.warning(f"AI evaluation failed for {issue.key}: {str(e)}")
        return RuleFinding(
            rule_id="ai.testability",
            rule_name="Testability",
            score=5.0,
            max_score=10.0,
            severity="info",
            finding="AI evaluation unavailable for this issue",
            suggestion="Please review the acceptance criteria manually for testability",
            field="acceptance_criteria"
        )
