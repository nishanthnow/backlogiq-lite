# BacklogIQ Lite — Quick Start Guide

## What You Have

You've built a complete Jira backlog quality analysis tool with:
- **Backend**: Python FastAPI with Jira Cloud integration
- **Frontend**: React with TypeScript + Tailwind CSS
- **Rules**: 7 fast sanity checks + 3 AI-powered evaluations (disabled by default)
- **Streaming**: Real-time SSE progress updates during analysis

**Initial Build**: Prompts 1-5 complete  
**Status**: Ready to test immediately  
**Next**: Prompt 6 adds Azure AD auth + persistence (optional)

---

## Step 1: Prerequisites

Before starting, make sure you have:

### Required
- **Python 3.12+** → Download from [python.org](https://www.python.org/downloads/)
- **Node.js 18+** → Download from [nodejs.org](https://nodejs.org/)
- **Git** → Download from [git-scm.com](https://git-scm.com/)

### Jira Setup
1. Go to https://www.atlassian.com/software/jira/free (sign up for free)
2. Create a project (e.g., "TEST") and add a few sample issues
3. Generate a Personal Access Token:
   - Go to https://id.atlassian.com/manage-profile/security/api-tokens
   - Click "Create API token"
   - Copy the token somewhere safe

### Optional: Azure OpenAI (for AI rules)
If you want to enable AI-powered analysis:
1. Create an Azure OpenAI account at https://azure.microsoft.com/en-us/products/cognitive-services/openai-service/
2. Deploy a GPT-4 model
3. Get your API key, endpoint, and deployment name

---

## Step 2: Install Dependencies

Open a terminal in the `backlogiq-lite` folder.

### Backend
```bash
cd backend
pip install -r requirements.txt
```

### Frontend
```bash
cd ../frontend
npm install
```

---

## Step 3: Configure Environment

### Backend Configuration

Copy `.env.example` to `.env`:
```bash
cd backend
cp .env.example .env
```

Edit `backend/.env` with your Azure OpenAI credentials:
```
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_API_KEY=your-api-key-here
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
SECRET_KEY=generate-with-python-command-below
CORS_ORIGINS=http://localhost:5173
```

Generate a SECRET_KEY:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

## Step 4: Run the Services

### Terminal 1: Backend
```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

You should see:
```
Uvicorn running on http://127.0.0.1:8000
```

### Terminal 2: Frontend
```bash
cd frontend
npm run dev
```

You should see:
```
  VITE v5.0.8  ready in 123 ms

  ➜  Local:   http://localhost:5173/
  ➜  press h to show help
```

---

## Step 5: Test It

1. **Open browser**: http://localhost:5173
2. **Fill in the form**:
   - **Jira Cloud URL**: `https://yourname.atlassian.net`
   - **Personal Access Token**: Paste your PAT from step 1
   - **Project Key**: Your Jira project key (e.g., `TEST`)
   - **Issue Types**: Story + Epic (✓ both)
   - **Max Issues**: 50 (for testing)

3. **Click "Analyze Backlog"**
4. **Watch the progress**:
   - "Connecting to Jira..."
   - "Fetching issues..."
   - "Running quality checks... (X/50)"
5. **See the results**:
   - Overall score (0-100)
   - Issue table with scores and findings
   - Expand any issue to see detailed recommendations

---

## What the Rules Check

### Fast Rules (instant)
1. **Description Exists** — Is there a description?
2. **Description Length** — Is it detailed enough?
3. **Acceptance Criteria** — Are there testable criteria?
4. **Story Title Format** — Does it follow "As a..., I want..., so that..." format?
5. **Title Length** — Is it not too long/short?
6. **Story Points Assigned** — Are estimates set?
7. **Not Oversized** — Are stories <= 13 points?

### AI Rules (optional, if enabled)
1. **Story Independence** — Can it be completed independently?
2. **Value Clarity** — Is the business value clear?
3. **Testability** — Are the acceptance criteria specific enough?

---

## Enabling AI Rules

To enable AI-powered analysis, edit `backend/app/main.py`:

Find this section:
```python
ai_client = None
ai_semaphore = None
try:
    # Uncomment to enable AI rules
    # ai_client = get_ai_client(settings)
    # ai_semaphore = asyncio.Semaphore(5)
    pass
```

Uncomment the lines:
```python
ai_client = None
ai_semaphore = None
try:
    # Uncomment to enable AI rules
    ai_client = get_ai_client(settings)
    ai_semaphore = asyncio.Semaphore(5)
```

Also in the `analyze_stream` function, change:
```python
results = []

# Process issues in batches
batch_size = 10
for batch_idx in range(0, len(issues), batch_size):
    batch = issues[batch_idx:batch_idx+batch_size]
    
    async def analyze_one(issue):
        return await run_all_rules(
            issue,
            ai_enabled=False,  # ← Change to True
            ...
        )
```

Restart the backend to apply changes.

---

## File Structure

```
backlogiq-lite/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI app
│   │   ├── config.py         # Settings
│   │   ├── schemas.py        # Pydantic models
│   │   ├── jira_client.py    # Jira API integration
│   │   └── rules/
│   │       ├── __init__.py
│   │       ├── fast_rules.py    # 7 sanity checks
│   │       ├── ai_rules.py      # 3 AI evaluations
│   │       └── runner.py        # Rule orchestration
│   ├── requirements.txt
│   ├── .env.example
│   └── .env (create from .env.example)
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── index.css
│   │   ├── types.ts
│   │   ├── api/
│   │   │   └── client.ts
│   │   └── components/
│   │       ├── Header.tsx
│   │       ├── ConnectionForm.tsx
│   │       ├── ProgressBar.tsx
│   │       ├── ScoreOverview.tsx
│   │       ├── IssueDetail.tsx
│   │       ├── IssuesTable.tsx
│   │       └── FindingCard.tsx
│   ├── vite.config.ts
│   ├── tsconfig.json
│   ├── tailwind.config.ts
│   ├── postcss.config.js
│   ├── index.html
│   ├── package.json
│   └── .gitignore
│
├── .gitignore
├── Makefile
└── README.md
```

---

## Troubleshooting

### "Connection refused" when trying to analyze
- Make sure backend is running on http://localhost:8000
- Check that frontend proxy is configured (vite.config.ts)

### "Invalid Jira URL or Personal Access Token"
- Verify your URL ends with `.atlassian.net` (not `atlassian.com`)
- Make sure PAT is current (tokens expire; generate a new one)
- Check that the PAT has "read:jira-work" scope

### "No issues found"
- Verify the project key is correct (case-sensitive usually)
- Make sure your Jira Cloud instance has issues in that project
- Check that you have view permissions on the project

### SSE progress not showing
- Check browser DevTools (F12) → Network tab
- See if `/api/analyze?stream=true` shows a 200 response
- Look at Console tab for any errors

### "CORS error"
- Make sure `CORS_ORIGINS` in `.env` includes `http://localhost:5173`
- Restart the backend after changing `.env`

---

## Next Steps: Prompt 6 (Optional)

Prompt 6 adds:
- **Azure AD Single Sign-On** (users log in with Microsoft accounts)
- **SQLite Database** (persistent analysis history)
- **Encrypted PAT Storage** (save Jira connections securely)
- **User Accounts** (track who analyzed what)

To implement Prompt 6, you'll need:
1. Azure AD app registration (Microsoft Entra)
2. msal (Microsoft Authentication Library)
3. SQLAlchemy + SQLite
4. Encryption for PAT storage

See the original `backlogiq-lite-prompts.md` file for full Prompt 6 details.

---

## Making It Production-Ready

For a real deployment:

1. **Docker**: Use Docker Compose to containerize both services
2. **Database**: Migrate from SQLite to PostgreSQL or SQL Server
3. **Auth**: Implement Azure AD OIDC as outlined in Prompt 6
4. **HTTPS**: Use a real certificate (not localhost)
5. **Secrets**: Use Azure Key Vault (not .env files)
6. **Logging**: Add structured logging (not print statements)
7. **Monitoring**: Add Application Insights or similar
8. **CI/CD**: Set up GitHub Actions for automated testing
9. **Error Handling**: Improve error messages and recovery
10. **Rate Limiting**: Prevent abuse of Jira API

---

## Key Concepts

### How Analysis Works

1. **User submits** Jira URL + PAT + project key
2. **Backend validates** the PAT by calling Jira `/myself` endpoint
3. **Backend fetches** issues using JQL: `project = KEY AND issuetype in (Story, Epic)`
4. **Backend streams progress** to frontend via SSE
5. **For each issue**:
   - Converts Atlassian Document Format (ADF) to plain text
   - Extracts acceptance criteria from description
   - Runs 7 fast rules (checks fields, formats, length)
   - Optionally runs 3 AI rules (OpenAI evaluations)
   - Combines findings into a score
6. **Frontend displays** results with sorting, filtering, expandable details

### Rule Scoring

Each rule returns:
- **Score** (0-10) — How well the issue meets the criterion
- **Severity** (critical/moderate/info) — Impact level
- **Finding** — What was observed
- **Suggestion** — How to improve

Overall issue score = average of all applicable rule scores × 10

Overall project score = average of all issue scores

---

## Support & Feedback

If you encounter issues:
1. Check the troubleshooting section above
2. Review browser console (F12) for errors
3. Check backend terminal for error messages
4. Verify `.env` is correctly configured

---

## Building Out Further

Ideas for enhancements:
- **Trend Tracking**: Compare backlog health week-over-week
- **Team Reports**: Group issues by assignee or epic
- **Automations**: Automatically comment findings back to Jira
- **Custom Rules**: Let users create their own checks
- **Bulk Actions**: Apply suggestions to multiple issues
- **Templates**: Save and reuse project configurations
- **Integrations**: Slack notifications, Jira webhooks

---

Happy analyzing! 🚀
