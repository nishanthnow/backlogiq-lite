# Prompt 6: Auth & Persistence (Implementation Guide)

This file provides a roadmap and starter code for implementing Prompt 6 features.

## Overview

Prompt 6 adds:
1. **Azure AD OIDC Authentication** - Users login with Microsoft accounts
2. **SQLite Database** - Persistent storage of user data and analysis history
3. **Token Encryption** - Securely store Jira PATs
4. **User Management** - Track who ran which analyses

---

## What's Implemented in Prompts 1-5

✅ Stateless Jira analysis  
✅ Real-time progress streaming (SSE)  
✅ 7 fast + 3 AI rules  
✅ Beautiful React UI  

## What Prompt 6 Adds

🔄 User authentication (Azure AD)  
🔄 Database persistence (SQLite → SQL Server later)  
🔄 Saved connections (encrypted PATs)  
🔄 Analysis history  
🔄 User profiles & logout  

---

## Implementation Steps

### Step 1: Install New Dependencies

```bash
# In backend/
pip install msal python-jose[cryptography] sqlalchemy[asyncio] aiosqlite

# Also update requirements.txt with:
msal==1.31.0
python-jose[cryptography]==3.3.0
cryptography==43.0.0
sqlalchemy[asyncio]==2.0.35
aiosqlite==0.20.0
```

### Step 2: Create Azure AD App Registration

1. Go to https://portal.azure.com
2. Search for "App registrations"
3. Click "New registration"
4. Fill in:
   - **Name**: BacklogIQ Lite
   - **Redirect URI**: http://localhost:8000/api/auth/callback
5. Note the:
   - **Client ID** (Application ID)
   - **Tenant ID** (Directory ID)
6. Create a client secret:
   - Go to Certificates & secrets
   - Click "New client secret"
   - Copy the secret value (not ID)

### Step 3: Update Backend Configuration

Create/update `backend/.env`:
```
# Existing settings
AZURE_OPENAI_ENDPOINT=...
AZURE_OPENAI_API_KEY=...
AZURE_OPENAI_DEPLOYMENT_NAME=...
SECRET_KEY=...
CORS_ORIGINS=...

# NEW: Azure AD Settings
AZURE_AD_TENANT_ID=your-tenant-id
AZURE_AD_CLIENT_ID=your-client-id
AZURE_AD_CLIENT_SECRET=your-client-secret
AZURE_AD_REDIRECT_URI=http://localhost:8000/api/auth/callback

# NEW: Database
DATABASE_URL=sqlite+aiosqlite:///./backlogiq.db

# NEW: Encryption
JIRA_ENCRYPTION_KEY=encryption-key-32-chars-min
```

Generate encryption key:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### Step 4: Create SQLAlchemy Models

Create `backend/app/models.py`:

```python
from sqlalchemy import Column, String, Integer, DateTime, LargeBinary, Float
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
from datetime import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(String, primary_key=True)
    email = Column(String, unique=True, index=True)
    name = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

class SavedToken(Base):
    __tablename__ = "saved_tokens"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    alias = Column(String)
    jira_url = Column(String)
    encrypted_pat = Column(LargeBinary)  # nonce + ciphertext + tag
    is_valid = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class AnalysisHistory(Base):
    __tablename__ = "analysis_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String, index=True)
    jira_url = Column(String)
    project_key = Column(String)
    overall_score = Column(Float)
    total_issues = Column(Integer)
    critical_count = Column(Integer)
    moderate_count = Column(Integer)
    info_count = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

# Database initialization
async_engine = None
AsyncSessionLocal = None

async def init_db(database_url: str):
    global async_engine, AsyncSessionLocal
    async_engine = create_async_engine(database_url, echo=False)
    AsyncSessionLocal = sessionmaker(
        async_engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

### Step 5: Create Encryption Module

Create `backend/app/crypto.py`:

```python
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2
from cryptography.hazmat.primitives import hashes
import os

def encrypt_token(plaintext: str, master_key: str) -> bytes:
    """
    Encrypt a token using AES-256-GCM.
    Returns: nonce (12 bytes) + ciphertext + tag
    """
    # Derive key from master key
    salt = os.urandom(16)
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(master_key.encode())
    
    # Encrypt with random nonce
    nonce = os.urandom(12)
    cipher = AESGCM(key)
    ciphertext = cipher.encrypt(nonce, plaintext.encode(), None)
    
    # Return: salt + nonce + ciphertext
    return salt + nonce + ciphertext

def decrypt_token(encrypted_data: bytes, master_key: str) -> str:
    """Decrypt a token encrypted with encrypt_token."""
    salt = encrypted_data[:16]
    nonce = encrypted_data[16:28]
    ciphertext = encrypted_data[28:]
    
    # Derive same key
    kdf = PBKDF2(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = kdf.derive(master_key.encode())
    
    # Decrypt
    cipher = AESGCM(key)
    plaintext = cipher.decrypt(nonce, ciphertext, None)
    
    return plaintext.decode()
```

### Step 6: Create Authentication Module

Create `backend/app/auth.py`:

```python
from datetime import datetime, timedelta
from msal import ConfidentialClientApplication
from jose import JWTError, jwt
from fastapi import Depends, HTTPException, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from .config import settings
from .models import User, get_db, AsyncSessionLocal

class AuthManager:
    def __init__(self):
        self.app = ConfidentialClientApplication(
            settings.AZURE_AD_CLIENT_ID,
            authority=f"https://login.microsoftonline.com/{settings.AZURE_AD_TENANT_ID}",
            client_credential=settings.AZURE_AD_CLIENT_SECRET,
        )
    
    def get_auth_code_flow_url(self) -> str:
        """Get the URL user should visit to login."""
        return self.app.get_authorization_request_url(
            scopes=["openid", "profile", "email"],
            redirect_uri=settings.AZURE_AD_REDIRECT_URI,
        )
    
    def get_token_from_auth_code(self, code: str, redirect_uri: str) -> dict:
        """Exchange authorization code for tokens."""
        result = self.app.acquire_token_by_authorization_code(
            code,
            scopes=["openid", "profile", "email"],
            redirect_uri=redirect_uri,
        )
        
        if "error" in result:
            raise Exception(f"Auth failed: {result['error']}")
        
        return result

auth_manager = AuthManager()

def create_jwt(user_id: str, email: str, name: str) -> str:
    """Create a JWT token for API access."""
    payload = {
        "user_id": user_id,
        "email": email,
        "name": name,
        "exp": datetime.utcnow() + timedelta(hours=8),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")

async def get_current_user(
    authorization: str = Header(None),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Extract and validate JWT from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing authorization header")
    
    token = authorization.replace("Bearer ", "")
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = payload.get("user_id")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    # Load user from DB
    stmt = select(User).where(User.user_id == user_id)
    result = await db.execute(stmt)
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user
```

### Step 7: Add Auth Endpoints

Add to `backend/app/main.py`:

```python
from fastapi import Query
from .auth import auth_manager, create_jwt, get_current_user
from .models import User, init_db, AsyncSessionLocal
from .crypto import encrypt_token, decrypt_token

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db(settings.DATABASE_URL)

@app.get("/api/auth/login")
async def login():
    """Get Azure AD login URL."""
    auth_url = auth_manager.get_auth_code_flow_url()
    return {"auth_url": auth_url}

@app.get("/api/auth/callback")
async def auth_callback(
    code: str = Query(...),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    """Handle Azure AD callback after login."""
    try:
        token_result = auth_manager.get_token_from_auth_code(
            code,
            settings.AZURE_AD_REDIRECT_URI
        )
        
        # Extract user info from ID token
        id_token_claims = token_result.get("id_token_claims", {})
        user_id = id_token_claims.get("oid")
        email = id_token_claims.get("email")
        name = id_token_claims.get("name")
        
        # Create/update user in DB
        # (Simplified — would use proper upsert in real code)
        user = User(user_id=user_id, email=email, name=name)
        # await db.merge(user)  # Upsert
        # await db.commit()
        
        # Create JWT for API access
        jwt_token = create_jwt(user_id, email, name)
        
        # Redirect to frontend with token
        return {
            "token": jwt_token,
            "user": {"email": email, "name": name}
        }
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/auth/me")
async def get_me(current_user: User = Depends(get_current_user)):
    """Get current user info."""
    return {
        "user_id": current_user.user_id,
        "email": current_user.email,
        "name": current_user.name,
        "last_login": current_user.last_login.isoformat(),
    }

@app.post("/api/tokens")
async def save_token(
    request: AnalyzeRequest,
    alias: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(AsyncSessionLocal),
):
    """Save a Jira PAT (encrypted)."""
    # Validate PAT
    client = JiraCloudClient(request.jira_url, request.pat)
    try:
        await client.validate_token()
    except:
        raise HTTPException(status_code=400, detail="Invalid PAT")
    finally:
        await client.close()
    
    # Encrypt and store
    encrypted_pat = encrypt_token(request.pat, settings.JIRA_ENCRYPTION_KEY)
    
    saved_token = SavedToken(
        user_id=current_user.user_id,
        alias=alias,
        jira_url=request.jira_url,
        encrypted_pat=encrypted_pat,
    )
    db.add(saved_token)
    await db.commit()
    
    return {"id": saved_token.id, "alias": alias, "jira_url": request.jira_url}
```

### Step 8: Update Frontend for Auth

In `frontend/src/App.tsx`:

```typescript
useEffect(() => {
  // Check for token in URL (from auth callback)
  const params = new URLSearchParams(window.location.search)
  const token = params.get('token')
  if (token) {
    localStorage.setItem('auth_token', token)
    window.history.replaceState({}, '', '/')
  }
}, [])

// Add logout button to header
const handleLogout = () => {
  localStorage.removeItem('auth_token')
  // Redirect to login
  window.location.href = '/api/auth/login'
}

// Show login button if no token
if (!localStorage.getItem('auth_token')) {
  return <LoginPage />
}
```

---

## Testing Prompt 6

1. Start backend: `uvicorn app.main:app --reload`
2. Open frontend: http://localhost:5173
3. Click "Sign in with Microsoft"
4. Login with Microsoft account
5. You'll be redirected with a token
6. Frontend will function as before, but now authenticated
7. Your token is stored in localStorage
8. Each analysis is now associated with your user

---

## Production Considerations

- **Never store tokens in localStorage** → Use httpOnly cookies instead
- **Use HTTPS** → Don't send tokens over plain HTTP
- **Rotate secrets** → Change client secrets regularly
- **Rate limit auth** → Prevent brute force login attempts
- **Add 2FA** → Use Azure AD conditional access
- **Audit logging** → Track who accessed what when
- **Data retention** → Set policies for deleting old analyses

---

## Next Enhancements

After Prompt 6:
- [ ] Push findings back to Jira as comments
- [ ] Team collaboration (share analysis results)
- [ ] Configure custom rules per team
- [ ] Export as PDF or CSV
- [ ] Integration with Slack/Teams for notifications
- [ ] Mobile app for on-the-go analysis

---

## Questions?

Review the original `backlogiq-lite-prompts.md` for full Prompt 6 specification.
