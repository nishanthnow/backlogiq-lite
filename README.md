# BacklogIQ Lite

A single-page web app for analyzing Jira Cloud backlog quality. Submit your project key → get a scored report with actionable findings.

## What It Does

- **Connects to Jira Cloud** with Personal Access Token (PAT) authentication
- **Fetches and normalizes** all issues of specified types
- **Runs 7 fast sanity checks** (description, title format, story points, acceptance criteria, etc.)
- **Produces a scored report** with findings, sorted by severity, searchable and expandable
- **Instant execution** — no AI dependencies, no external API calls beyond Jira

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12 + FastAPI + httpx |
| Frontend | React 18 + TypeScript + Vite + Tailwind CSS |
| Database | SQLite (eventual; stateless for now) |
| Auth | Azure AD OIDC (future) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 20+
- Jira Cloud instance with admin access
- A `.env` file with required credentials (see below)

### Setup

1. **Clone and install**:
   ```bash
   cd backlogiq-lite
   make install-backend
   make install-frontend
   ```

2. **Create `.env` in the `backend/` folder**:
   ```
   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
   CORS_ORIGINS=http://localhost:5173
   ```

3. **Generate Jira Personal Access Token**:
   - Go to: https://id.atlassian.com/manage-profile/security/api-tokens
   - Click **Create API token**
   - Copy the token (you'll paste it in the app UI)

4. **Run both services** (Terminal 1 and 2):
   ```bash
   # Terminal 1: Backend (FastAPI on port 8000)
   make dev-backend
   
   # Terminal 2: Frontend (React on port 5173)
   make dev-frontend
   ```

5. **Open your browser**:
   ```
   http://localhost:5173
   ```

### First Analysis

1. Enter your **Jira Cloud URL** (e.g., `https://mycompany.atlassian.net`)
2. Paste your **Personal Access Token**
3. Enter your **Project Key** (e.g., `PROJ`)
4. Select issue types (defaults: Epic, Story)
5. Click **Analyze Backlog**

The backend will:
- Validate your PAT with Jira
- Fetch issues using JQL
- Run 7 quality checks instantly
- Return a detailed report with scores and suggestions

## The 7 Fast Rules

BacklogIQ runs instant, rule-based checks on each issue:

1. **Description Exists** — Issue must have meaningful description text (>10 chars)
2. **Description Detail** — Description should be 200+ characters for full context
3. **Acceptance Criteria** — Stories should have acceptance criteria (Given/When/Then format)
4. **Story Title Format** — Stories should follow "As a [role], I want [goal], so that [benefit]" format
5. **Title Length** — Titles should be 10–80 characters (clear but not verbose)
6. **Story Points Assigned** — Stories must have story points for sprint planning
7. **Story Sizing** — Stories with 13+ points should be decomposed into smaller stories

## Architecture

### Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app + /api/analyze endpoint
│   ├── config.py            # Settings from .env
│   ├── schemas.py           # Pydantic request/response models
│   ├── jira_client.py       # Jira Cloud API client + ADF converter
│   └── rules/
│       ├── __init__.py
│       ├── fast_rules.py    # The 7 sanity check rules
│       └── runner.py        # Orchestrates rule execution
├── requirements.txt         # Python dependencies
└── .env.example             # Template for environment variables
```

### Frontend Structure

```
frontend/
├── src/
│   ├── App.tsx                  # Main app container + state
│   ├── types.ts                 # TypeScript interfaces
│   ├── api/
│   │   └── client.ts            # Axios + SSE streaming client
│   └── components/
│       ├── Header.tsx           # Top bar with branding
│       ├── ConnectionForm.tsx   # Jira URL/PAT/project key form
│       ├── ScoreOverview.tsx    # Overall score circle + stats
│       ├── IssuesTable.tsx      # Sortable, filterable issue list
│       ├── IssueDetail.tsx      # Expanded issue findings
│       ├── FindingCard.tsx      # Individual rule finding card
│       └── ProgressBar.tsx      # Real-time analysis progress
├── package.json
├── vite.config.ts
└── tailwind.config.ts
```

## Development

```
frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx           # Main component
│   ├── api/
│   │   └── client.ts     # Axios HTTP client
│   ├── components/       # React components
│   ├── types.ts          # TypeScript types
│   └── index.css         # Tailwind setup
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

## API Endpoints

### POST /api/analyze

Analyze a Jira backlog.

**Request**:
```json
{
  "jira_url": "https://myorg.atlassian.net",
  "pat": "your_personal_access_token",
  "project_key": "PROJ",
  "issue_types": ["Story", "Epic"],
  "max_issues": 200
}
```

**Response**:
```json
{
  "overall_score": 62.5,
  "total_issues": 42,
  "severity_breakdown": {"critical": 5, "moderate": 20, "info": 17},
  "issues": [
    {
      "issue_key": "PROJ-123",
      "issue_url": "https://myorg.atlassian.net/browse/PROJ-123",
      "issue_type": "Story",
      "issue_title": "As a user, I want...",
      "score": 75.0,
      "severity": "moderate",
      "findings": [
        {
          "rule_id": "fast.desc_length",
          "rule_name": "Description Length",
          "score": 5,
          "max_score": 10,
          "severity": "moderate",
          "finding": "Description is only 45 characters.",
          "suggestion": "Expand with context, constraints, and acceptance criteria.",
          "field": "description"
        }
      ]
    }
  ],
  "analyzed_at": "2026-03-05T14:30:00Z"
}
```

### GET /health

Health check.

**Response**: `{"status": "ok"}`

## Roadmap

### Current (Prompt 1-6)
- ✅ Project setup + Jira client (Prompt 1)
- ⏳ Fast rules (Prompt 2)
- ⏳ AI rules (Prompt 3)
- ⏳ React frontend (Prompt 4)
- ⏳ SSE progress streaming (Prompt 5)
- ⏳ Azure AD + persistence (Prompt 6)

### Future
- Jira Data Center support
- Push findings back to Jira as comments
- AI-powered backlog item generation
- PDF/CSV export
- Rule configuration UI
- RBAC for team access

## Contributing

Feedback and PRs welcome! Please test against a real Jira Cloud instance.

## License

Proprietary — BacklogIQ product.
