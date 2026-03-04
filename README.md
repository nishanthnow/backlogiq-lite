# BacklogIQ Lite

A single-page web app for analyzing Jira Cloud backlog quality. Submit your project key → get a scored report with actionable findings.

## What It Does

- **Connects to Jira Cloud** with Personal Access Token authentication
- **Fetches and normalizes** all issues of specified types
- **Runs 7 fast sanity checks** (description, title format, story points, etc.)
- **Runs 3 AI-powered evaluations** using Azure OpenAI GPT-4
- **Produces a scored report** with findingsSorted by severity, searchable, expandable

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python 3.12 + FastAPI + httpx |
| Frontend | React 18 + TypeScript + Vite + Tailwind |
| Database | SQLite (eventually; for now stateless) |
| AI | Azure OpenAI (GPT-4) |
| Auth | Azure AD OIDC (eventual) |

## Quick Start

### Prerequisites

- Python 3.12+
- Node.js 18+ (for frontend)
- Jira Cloud account with admin access
- Azure OpenAI account with GPT-4 deployed
- A `.env` file with required credentials (see below)

### Setup

1. **Clone and install**:
   ```bash
   cd backlogiq-lite
   make install-backend
   make install-frontend
   ```

2. **Create `.env` in `backend/` folder**:
   ```
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_API_KEY=your-api-key
   AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
   SECRET_KEY=<generate with: python -c "import secrets; print(secrets.token_urlsafe(32))">
   CORS_ORIGINS=http://localhost:5173
   ```

3. **Generate Jira Personal Access Token**:
   - Go to: https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Copy the token (you'll use it in the UI)

4. **Run both services**:
   ```bash
   # Terminal 1
   make dev-backend
   
   # Terminal 2
   make dev-frontend
   ```

5. **Open browser**:
   - http://localhost:5173

### First Run

1. Enter your **Jira Cloud URL** (e.g., `https://mycompany.atlassian.net`)
2. Paste your **Personal Access Token**
3. Enter your **Project Key** (e.g., `PROJ`)
4. Select issue types
5. Click **Analyze Backlog**

The backend will:
- Validate your PAT
- Fetch issues via JQL
- Run quality checks
- Display a report with scores and suggestions

## Development

### Backend Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py           # FastAPI app + endpoints
│   ├── config.py         # Settings from .env
│   ├── schemas.py        # Pydantic models
│   ├── jira_client.py    # Jira Cloud API client
│   ├── rules/            # Quality check rules (Prompt 2+)
│   └── models.py         # SQLAlchemy models (Prompt 6)
├── requirements.txt
└── .env.example
```

### Frontend Structure

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
