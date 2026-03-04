import httpx
import json
from typing import Optional
from .schemas import JiraIssue


def adf_to_plain_text(adf_node: Optional[dict]) -> str:
    """
    Convert Atlassian Document Format (ADF) to plain text.
    ADF is a JSON tree structure used by Jira for rich text fields.
    """
    if not adf_node:
        return ""
    
    if isinstance(adf_node, str):
        return adf_node
    
    if not isinstance(adf_node, dict):
        return ""
    
    text_parts = []
    
    # Handle text nodes directly
    if adf_node.get("type") == "text":
        return adf_node.get("text", "")
    
    # Handle nodes with content arrays
    if "content" in adf_node:
        for child in adf_node["content"]:
            text_parts.append(adf_to_plain_text(child))
    
    # Handle hardbreak nodes
    if adf_node.get("type") == "hardBreak":
        text_parts.append("\n")
    
    # Join with appropriate separators based on node type
    node_type = adf_node.get("type", "")
    if node_type in ["paragraph", "heading1", "heading2", "heading3", "codeBlock"]:
        separator = "\n\n"
    elif node_type in ["listItem"]:
        separator = "\n"
    else:
        separator = ""
    
    result = separator.join([p for p in text_parts if p])
    
    # Add newlines around certain block elements
    if node_type in ["paragraph", "heading1", "heading2", "heading3"]:
        if result:
            result = result + "\n\n"
    
    return result


def extract_acceptance_criteria(description_text: str) -> Optional[str]:
    """
    Extract acceptance criteria from description text.
    Looks for:
    1. A section starting with "Acceptance Criteria" (case-insensitive)
    2. Lines containing "Given/When/Then" patterns (BDD format)
    """
    if not description_text:
        return None
    
    lines = description_text.split("\n")
    criteria_section = []
    in_criteria = False
    
    for i, line in enumerate(lines):
        # Check if we're entering acceptance criteria section
        if "acceptance criteria" in line.lower():
            in_criteria = True
            continue
        
        # If we found the section, collect lines until next section or end
        if in_criteria:
            # Stop at next section heading (lines that look like headers)
            if line.strip() and line.strip()[0].isupper() and line.count(" ") < 5 and i > 0:
                if lines[i-1].strip() == "":
                    break
            criteria_section.append(line)
        
        # Also check for BDD format anywhere
        if line.strip().startswith(("Given", "When", "Then", "And", "But")):
            if not in_criteria:
                criteria_section.append(line)
                in_criteria = True
    
    criteria_text = "\n".join(criteria_section).strip()
    return criteria_text if criteria_text else None


class JiraCloudClient:
    """Client for Jira Cloud REST API v3."""
    
    def __init__(self, base_url: str, pat: str):
        """
        Initialize Jira Cloud client.
        
        Args:
            base_url: Jira instance URL (e.g., https://yourorg.atlassian.net)
            pat: Personal Access Token for authentication
        """
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "Authorization": f"Bearer {pat}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            },
            timeout=httpx.Timeout(connect=10.0, read=30.0)
        )
    
    async def validate_token(self) -> dict:
        """
        Validate the PAT by calling /rest/api/3/myself.
        Returns user information or raises an exception.
        """
        response = await self.client.get("/rest/api/3/myself")
        response.raise_for_status()
        return response.json()
    
    async def fetch_issues(
        self,
        project_key: str,
        issue_types: list[str],
        max_issues: int = 200
    ) -> list[JiraIssue]:
        """
        Fetch issues from a Jira project using JQL.
        
        Args:
            project_key: Jira project key (e.g., "PROJ")
            issue_types: List of issue types to fetch (e.g., ["Story", "Epic"])
            max_issues: Maximum number of issues to return
        
        Returns:
            List of normalized JiraIssue objects
        """
        # Build JQL query
        types_str = ", ".join([f'"{t}"' for t in issue_types])
        jql = f'project = "{project_key}" AND issuetype in ({types_str})'
        
        all_issues = []
        start_at = 0
        
        while len(all_issues) < max_issues:
            remaining = max_issues - len(all_issues)
            max_results = min(100, remaining)
            
            response = await self.client.get(
                "/rest/api/3/search",
                params={
                    "jql": jql,
                    "startAt": start_at,
                    "maxResults": max_results,
                    "fields": [
                        "summary",
                        "issuetype",
                        "status",
                        "description",
                        "customfield_10016",  # Story Points
                        "labels",
                        "assignee"
                    ]
                }
            )
            response.raise_for_status()
            data = response.json()
            
            issues = data.get("issues", [])
            if not issues:
                break
            
            for issue in issues:
                # Skip if we've reached max
                if len(all_issues) >= max_issues:
                    break
                
                # Extract and normalize field values
                key = issue["key"]
                fields = issue["fields"]
                
                # Description: convert from ADF to plain text
                description_adf = fields.get("description")
                description_text = adf_to_plain_text(description_adf)
                
                # Extract acceptance criteria
                acceptance_criteria = extract_acceptance_criteria(description_text)
                
                # Story points (null if not assigned)
                story_points = None
                if fields.get("customfield_10016"):
                    try:
                        story_points = float(fields["customfield_10016"])
                    except (ValueError, TypeError):
                        story_points = None
                
                # Assignee (display name)
                assignee = None
                if fields.get("assignee"):
                    assignee = fields["assignee"].get("displayName")
                
                # Build Jira URL
                url = f"{self.base_url}/browse/{key}"
                
                # Create JiraIssue object
                jira_issue = JiraIssue(
                    key=key,
                    summary=fields.get("summary", ""),
                    issue_type=fields.get("issuetype", {}).get("name", ""),
                    status=fields.get("status", {}).get("name", ""),
                    description_text=description_text,
                    acceptance_criteria=acceptance_criteria,
                    story_points=story_points,
                    labels=fields.get("labels", []),
                    assignee=assignee,
                    url=url
                )
                
                all_issues.append(jira_issue)
            
            start_at += max_results
            
            # If we got fewer results than requested, we've reached the end
            if len(issues) < max_results:
                break
        
        return all_issues
    
    async def close(self):
        """Close the HTTP client connection."""
        await self.client.aclose()
