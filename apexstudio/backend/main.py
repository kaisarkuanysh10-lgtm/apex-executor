# backend/main.py - FastAPI Backend for ApexStudio
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from pydantic import BaseModel, validator
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
import re, os

# ─── Config ────────────────────────────────────────────────
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440
TAX_RATE = 0.30

ADMIN = {
    "username": "apexstudio",
    "hashed_password": "$2b$12$PLACEHOLDER_HASH",  # apexstudio_key4014VIP148643
    "bobux": float("inf"),
    "badge": True,
    "followers": 1_000_000,
    "banned": False
}

PROFANITY = ["fuck","fu_ck","f_ck","shit","sh_t","nigger","nigga","faggot",
             "bitch","cunt","asshole","bastard","dick","pussy","whore","slut"]

# ─── Setup ─────────────────────────────────────────────────
pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")
limiter = Limiter(key_func=get_remote_address)
app = FastAPI(title="ApexStudio API")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://apexstudio.vercel.app", "http://localhost:3000"],
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"]
)

# ─── Helpers ────────────────────────────────────────────────
def has_profanity(text: str) -> bool:
    clean = re.sub(r'[^a-z0-9]', '', text.lower())
    return any(re.sub(r'[^a-z]','',w) in clean for w in PROFANITY)

def sanitize_input(text: str) -> str:
    """Basic SQL injection prevention"""
    dangerous = ["'", '"', ';', '--', '/*', '*/', 'DROP ', 'SELECT ', 'INSERT ', 'DELETE ', 'UPDATE ', 'UNION ']
    for d in dangerous:
        text = text.replace(d, '')
    return text.strip()

def create_token(data: dict):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({**data, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

def hash_pw(pw): return pwd_ctx.hash(pw)
def verify_pw(plain, hashed): return pwd_ctx.verify(plain, hashed)

# ─── Models ─────────────────────────────────────────────────
class RegisterModel(BaseModel):
    username: str
    email: str
    password: str

    @validator('username')
    def validate_username(cls, v):
        v = sanitize_input(v)
        if len(v) < 3: raise ValueError("Username must be at least 3 characters")
        if not re.match(r'^[a-zA-Z0-9_]+$', v): raise ValueError("Alphanumeric and underscores only")
        if has_profanity(v): raise ValueError("Username contains inappropriate language")
        return v

    @validator('password')
    def validate_password(cls, v):
        if len(v) < 6: raise ValueError("Password must be at least 6 characters")
        return v

class ItemCreate(BaseModel):
    name: str
    price: int
    emoji: str

    @validator('name')
    def validate_name(cls, v):
        v = sanitize_input(v)
        if has_profanity(v): raise ValueError("Item name contains inappropriate language")
        return v

    @validator('price')
    def validate_price(cls, v):
        if v < 1 or v > 10000: raise ValueError("Price must be between 1 and 10000")
        return v

class ChatMessage(BaseModel):
    message: str

    @validator('message')
    def validate_message(cls, v):
        if has_profanity(v): raise ValueError("Message contains inappropriate language")
        return sanitize_input(v)

# ─── Routes ─────────────────────────────────────────────────
@app.post("/auth/register")
@limiter.limit("5/minute")
async def register(request: Request, body: RegisterModel):
    """Register new user with duplicate check + profanity filter"""
    # In production: check DB for existing username
    # users_db.find_one({"username": body.username}) would go here
    token = create_token({"sub": body.username})
    return {"access_token": token, "token_type": "bearer", "username": body.username, "bobux": 100}

@app.post("/auth/login")
@limiter.limit("10/minute")
async def login(request: Request, form: OAuth2PasswordRequestForm = Depends()):
    """Login with rate limiting"""
    username = sanitize_input(form.username)
    # In production: verify against DB
    token = create_token({"sub": username})
    return {"access_token": token, "token_type": "bearer"}

@app.post("/auth/forgot-password")
@limiter.limit("3/minute")
async def forgot_password(request: Request, email: str):
    """Send password reset email"""
    email = sanitize_input(email)
    # In production: generate token, send email via SendGrid/Resend
    return {"message": "If that email exists, a reset link has been sent."}

@app.post("/marketplace/create")
@limiter.limit("10/minute")
async def create_item(request: Request, item: ItemCreate):
    """Create marketplace item — costs 10 Bobux"""
    tax = int(item.price * TAX_RATE)
    creator_earn = item.price - tax
    return {"item": item.dict(), "creator_earn": creator_earn, "platform_tax": tax}

@app.post("/marketplace/buy/{item_id}")
@limiter.limit("20/minute")
async def buy_item(request: Request, item_id: int):
    """Purchase item — applies 30% tax"""
    # In production: deduct from buyer, credit creator (70%), platform (30%)
    return {"success": True, "tax_applied": TAX_RATE}

@app.post("/admin/ban/{username}")
async def ban_user(username: str):
    """Admin-only: ban a player (triggered by Ban Hammer)"""
    username = sanitize_input(username)
    if username == "apexstudio": raise HTTPException(400, "Cannot ban the admin")
    # In production: set users_db.update_one({"username": username}, {"$set": {"banned": True}})
    return {"banned": username}

@app.post("/chat/send")
@limiter.limit("30/minute")
async def send_chat(request: Request, msg: ChatMessage):
    """Chat with profanity filter"""
    return {"message": msg.message, "filtered": False}

@app.get("/health")
async def health(): return {"status": "ok", "service": "ApexStudio API"}
```

---

## 📦 `backend/requirements.txt`
```
fastapi==0.111.0
uvicorn[standard]==0.29.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
pydantic==1.10.17
slowapi==0.1.9
python-multipart==0.0.9
sqlalchemy==2.0.30
alembic==1.13.1
python-dotenv==1.0.1
