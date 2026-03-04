from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime
import asyncio
import json

from .config import settings
from .schemas import AnalyzeRequest, AnalysisReport, IssueAnalysis, RuleFinding
from .jira_client import JiraCloudClient
from .rules.runner import run_all_rules
from .rules.ai_rules import get_ai_client


app = FastAPI(title="BacklogIQ Lite")

# Add CORS middleware
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}


def sse_event(event_type: str, data: dict) -> str:
    """Format a Server-Sent Event message, stream: bool = True):
    """
    Analyze a Jira backlog and return a health report.
    
    Query parameters:
    - stream: bool (default True) — if True, returns SSE stream; if False, returns JSON
    
    This endpoint:
    1. Validates the Jira PAT
    2. Fetches issues from the specified project
    3. Runs quality checks on each issue
    4. Returns progress as SSE stream or final report as JSON
    """
    
    if stream:
        # Return SSE stream
        return StreamingResponse(
            analyze_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "X-Accel-Buffering": "no"
            }
        )
    else:
        # Return regular JSON response (for backwards compatibility)
        try:
            client = JiraCloudClient(request.jira_url, request.pat)
            
            try:
                await client.validate_token()
            except Exception as e:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid Jira URL or Personal Access Token. Please check your credentials."
                )
            
            try:
                issues = await client.fetch_issues(
                    request.project_key,
                    request.issue_types,
                    request.max_issues
                )
            except Exception as e:
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to fetch issues: {str(e)}"
                )
            
            if not issues:
                raise HTTPException(
                    status_code=404,
                    detail=f"No issues found for project {request.project_key} with types {request.issue_types}. "
                           f"Check the project key and ensure you have access."
                )
            
            # Run quality checks on each issue
            issue_analyses = []
            batch_size = 10
            for i in range(0, len(issues), batch_size):
                batch = issues[i:i+batch_size]
                
                async def analyze_one(issue):
                    return await run_all_rules(issue)
                
                batch_results = await asyncio.gather(*[analyze_one(iss) for iss in batch])
                issue_analyses.extend(batch_results)
            
            # Build report
            overall_score = sum(ia.score for ia in issue_analyses) / len(issue_analyses) if issue_analyses else 0
            
            severity_breakdown = {"critical": 0, "moderate": 0, "info": 0}
            for analysis in issue_analyses:
                severity_breakdown[analysis.severity] = severity_breakdown.get(analysis.severity, 0) + 1
            
            report = AnalysisReport(
                overall_score=round(overall_score, 1),
                total_issues=len(issues),
                severity_breakdown=severity_breakdown,
                issues=issue_analyses,
                analyzed_at=datetime.utcnow().isoformat() + "Z"
            )
            
            return report
            
        finally:
            if 'client' in locals():
                severity_breakdown[analysis.severity] = severity_breakdown.get(analysis.severity, 0) + 1
        
        overall_score = sum(ia.score for ia in results) / len(results) if results else 0
        
        report = AnalysisReport(
            overall_score=round(overall_score, 1),
            total_issues=len(issues),
            severity_breakdown=severity_breakdown,
            issues=results,
            analyzed_at=datetime.utcnow().isoformat() + "Z"
        )
        
        yield sse_event("complete", report.model_dump())
        
    except Exception as e:
        print(f"Error during analysis: {str(e)}")
        yield sse_event("error", {
            "message": f"Unexpected error: {str(e)}"
        })
    finally:
        if 'client' in locals():
            await client.close()


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest) -> AnalysisReport:
    """
    Analyze a Jira backlog and return a health report.
    
    This endpoint:
    1. Validates the Jira PAT
    2. Fetches issues from the specified project
    3. Runs quality checks on each issue
    4. Returns an analysis report with scores and findings
    """
    
    try:
        # Create Jira client and validate token
        client = JiraCloudClient(request.jira_url, request.pat)
        
        try:
            await client.validate_token()
        except Exception as e:
            raise HTTPException(
                status_code=401,
                detail="Invalid Jira URL or Personal Access Token. Please check your credentials."
            )
        
        # Fetch issues
        try:
            issues = await client.fetch_issues(
                request.project_key,
                request.issue_types,
                request.max_issues
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail=f"Failed to fetch issues: {str(e)}"
            )
        
        if not issues:
            raise HTTPException(
                status_code=404,
                detail=f"No issues found for project {request.project_key} with types {request.issue_types}. "
                       f"Check the project key and ensure you have access."
            )
        
        # Run quality checks on each issue
        # Initialize AI client if enabled
        ai_client = None
        ai_semaphore = None
        try:
            # Note: AI rules can be enabled by passing ai_enabled=True to run_all_rules
            # For now, we'll keep them disabled by default (ai_enabled=False)
            # To enable: uncomment the lines below and ensure Azure OpenAI credentials are set
            # ai_client = get_ai_client(settings)
            # ai_semaphore = asyncio.Semaphore(5)  # Max 5 concurrent OpenAI calls
            pass
        except Exception as e:
            print(f"Failed to initialize AI client: {e}")
            ai_client = None
        
        # Process issues in batches to avoid overwhelming resources
        issue_analyses = []
        batch_size = 10
        for i in range(0, len(issues), batch_size):
            batch = issues[i:i+batch_size]
            
            async def analyze_one(issue):
                return await run_all_rules(
                    issue,
                    ai_enabled=False,  # Set to True to enable AI rules
                    ai_client=ai_client,
                    ai_deployment=settings.AZURE_OPENAI_DEPLOYMENT_NAME,
                    ai_semaphore=ai_semaphore
                )
            
            batch_results = await asyncio.gather(*[analyze_one(iss) for iss in batch])
            issue_analyses.extend(batch_results)
        
        # Build report
        overall_score = sum(ia.score for ia in issue_analyses) / len(issue_analyses) if issue_analyses else 0
        
        severity_breakdown = {"critical": 0, "moderate": 0, "info": 0}
        for analysis in issue_analyses:
            severity_breakdown[analysis.severity] = severity_breakdown.get(analysis.severity, 0) + 1
        
        report = AnalysisReport(
            overall_score=round(overall_score, 1),
            total_issues=len(issues),
            severity_breakdown=severity_breakdown,
            issues=issue_analyses,
            analyzed_at=datetime.utcnow().isoformat() + "Z"
        )
        
        return report
        
    finally:
        if 'client' in locals():
            await client.close()
