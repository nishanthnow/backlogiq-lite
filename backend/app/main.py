from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from datetime import datetime, timezone
import asyncio
import json
import logging

from .config import settings
from .schemas import AnalyzeRequest, AnalysisReport
from .jira_client import JiraCloudClient
from .rules.runner import run_all_rules

logger = logging.getLogger("backlogiq")

app = FastAPI(title="BacklogIQ Lite", description="Backlog Quality Copilot")

# Add CORS middleware
cors_origins = [origin.strip() for origin in settings.CORS_ORIGINS.split(",")]
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("BacklogIQ Lite started — AI provider: none (fast rules only)")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok", "version": "0.1.0"}


def sse_event(event: str, data: dict) -> str:
    """Format a Server-Sent Event string."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def analyze_stream(request: AnalyzeRequest):
    """
    Generator that yields SSE events as analysis progresses.
    
    Emits events:
    - progress: with phase, message, current, total
    - complete: with full AnalysisReport
    - error: with error message
    """
    client = JiraCloudClient(request.jira_url, request.pat)
    
    try:
        # Phase: Connecting
        yield sse_event("progress", {
            "phase": "connecting",
            "message": "Validating Jira connection...",
            "current": 0,
            "total": 0,
        })
        
        try:
            await client.validate_token()
        except Exception:
            yield sse_event("error", {
                "message": "Invalid Jira URL or Personal Access Token. Please check your credentials."
            })
            return
        
        # Phase: Fetching
        yield sse_event("progress", {
            "phase": "fetching",
            "message": "Fetching issues from Jira...",
            "current": 0,
            "total": 0,
        })
        
        try:
            issues = await client.fetch_issues(
                request.project_key,
                request.issue_types,
                request.max_issues
            )
        except Exception as e:
            yield sse_event("error", {
                "message": f"Failed to fetch issues: {str(e)}"
            })
            return
        
        if not issues:
            yield sse_event("error", {
                "message": f"No issues found for project '{request.project_key}' with types {request.issue_types}. "
                           f"Check the project key and ensure you have access."
            })
            return
        
        yield sse_event("progress", {
            "phase": "fetching",
            "message": f"Found {len(issues)} issues",
            "current": 0,
            "total": len(issues),
        })
        
        # Phase: Analyzing
        results = []
        for i, issue in enumerate(issues):
            result = await run_all_rules(issue)
            results.append(result)
            
            # Add small delay so SSE events actually stream rather than arriving all at once
            await asyncio.sleep(0.01)
            
            yield sse_event("progress", {
                "phase": "analyzing",
                "message": f"Checking {issue.key}...",
                "current": i + 1,
                "total": len(issues),
            })
        
        # Phase: Complete
        overall_score = sum(r.score for r in results) / len(results) if results else 0.0
        
        severity_breakdown = {"critical": 0, "moderate": 0, "info": 0}
        for analysis in results:
            severity_breakdown[analysis.severity] = severity_breakdown.get(analysis.severity, 0) + 1
        
        report = AnalysisReport(
            overall_score=round(overall_score, 1),
            total_issues=len(issues),
            severity_breakdown=severity_breakdown,
            issues=results,
            analyzed_at=datetime.now(timezone.utc).isoformat(),
            ai_enabled=False,
        )
        
        yield sse_event("complete", report.model_dump())
    
    except Exception as e:
        yield sse_event("error", {"message": f"Analysis failed: {str(e)}"})
    
    finally:
        await client.close()


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest, stream: bool = False):
    """
    Analyze a Jira backlog.
    
    Query parameters:
    - stream (bool): If true, returns Server-Sent Events for real-time progress.
                     If false (default), returns complete AnalysisReport as JSON.
    
    This endpoint:
    1. Validates the Jira PAT
    2. Fetches issues from the specified project  
    3. Runs 7 fast sanity checks on each issue
    4. Returns an analysis report with scores and findings
    """
    
    if stream:
        return StreamingResponse(
            analyze_stream(request),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            },
        )
    else:
        # Non-streaming mode (for testing with curl/Postman)
        client = JiraCloudClient(request.jira_url, request.pat)
        
        try:
            # Validate token
            try:
                await client.validate_token()
            except Exception:
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
                    detail=f"No issues found for project '{request.project_key}' with types {request.issue_types}. "
                           f"Check the project key and ensure you have access."
                )
            
            # Run analysis on each issue
            issue_analyses = []
            for issue in issues:
                analysis = await run_all_rules(issue)
                issue_analyses.append(analysis)
            
            # Build report
            overall_score = sum(ia.score for ia in issue_analyses) / len(issue_analyses) if issue_analyses else 0.0
            
            severity_breakdown = {"critical": 0, "moderate": 0, "info": 0}
            for analysis in issue_analyses:
                severity_breakdown[analysis.severity] = severity_breakdown.get(analysis.severity, 0) + 1
            
            report = AnalysisReport(
                overall_score=round(overall_score, 1),
                total_issues=len(issues),
                severity_breakdown=severity_breakdown,
                issues=issue_analyses,
                analyzed_at=datetime.now(timezone.utc).isoformat(),
                ai_enabled=False,
            )
            
            return report
        
        finally:
            await client.close()
