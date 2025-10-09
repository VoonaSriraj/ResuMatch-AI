"""
Authentication endpoints for user registration, login, and OAuth
"""

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import Optional
import requests

from app.database import get_db
from app.models.user import User
from app.models.activity_log import ActivityLog
from app.utils.auth import (
    authenticate_user, create_user_token, get_password_hash,
    get_current_active_user
)
from app.config import settings
from app.utils.logger import get_logger

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)

# Pydantic models
class UserRegister(BaseModel):
    name: str
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    subscription_plan: str
    is_verified: bool

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class LinkedInAuthRequest(BaseModel):
    code: str
    state: Optional[str] = None

class OAuthCode(BaseModel):
    code: str
    state: Optional[str] = None

@router.post("/register", response_model=TokenResponse)
async def register_user(user_data: UserRegister, db: Session = Depends(get_db)):
    """Register a new user"""
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.email == user_data.email).first()
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        hashed_password = get_password_hash(user_data.password)
        new_user = User(
            name=user_data.name,
            email=user_data.email,
            hashed_password=hashed_password,
            subscription_plan="free"
        )
        
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Log activity
        activity = ActivityLog(
            user_id=new_user.id,
            action_type="user_registration",
            description=f"User registered with email: {user_data.email}"
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"New user registered: {user_data.email}")
        
        return create_user_token(new_user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    """Login user with email and password"""
    try:
        user = authenticate_user(db, user_data.email, user_data.password)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Log activity
        activity = ActivityLog(
            user_id=user.id,
            action_type="user_login",
            description=f"User logged in: {user_data.email}"
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"User logged in: {user_data.email}")
        
        return create_user_token(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """Get current user information"""
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        subscription_plan=current_user.subscription_plan,
        is_verified=current_user.is_verified
    )

@router.post("/linkedin", response_model=TokenResponse)
async def linkedin_oauth(
    auth_request: LinkedInAuthRequest,
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle LinkedIn OAuth callback"""
    try:
        if not settings.linkedin_client_id or not settings.linkedin_client_secret:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="LinkedIn OAuth not configured"
            )
        
        # Exchange code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        token_data = {
            "grant_type": "authorization_code",
            "code": auth_request.code,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
            "redirect_uri": settings.linkedin_redirect_uri
        }
        
        token_response = requests.post(token_url, data=token_data)
        if token_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        access_token = token_response.json().get("access_token")
        
        # Get user profile from LinkedIn
        profile_url = "https://api.linkedin.com/v2/people/~"
        profile_response = requests.get(
            profile_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if profile_response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get LinkedIn profile"
            )
        
        profile_data = profile_response.json()
        
        # Get email from LinkedIn
        email_url = "https://api.linkedin.com/v2/emailAddress?q=members&projection=(elements*(handle~))"
        email_response = requests.get(
            email_url,
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        email_data = email_response.json()
        email = None
        if email_response.status_code == 200 and email_data.get("elements"):
            email = email_data["elements"][0]["handle~"]["emailAddress"]
        
        if not email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Could not retrieve email from LinkedIn"
            )
        
        # Check if user exists
        user = db.query(User).filter(User.email == email).first()
        
        if user:
            # Update existing user with LinkedIn info
            user.linkedin_id = profile_data.get("id")
            user.linkedin_access_token = access_token
            user.name = profile_data.get("localizedFirstName", "") + " " + profile_data.get("localizedLastName", "")
        else:
            # Create new user
            user = User(
                name=profile_data.get("localizedFirstName", "") + " " + profile_data.get("localizedLastName", ""),
                email=email,
                linkedin_id=profile_data.get("id"),
                linkedin_access_token=access_token,
                subscription_plan="free",
                is_verified=True
            )
            db.add(user)
        
        db.commit()
        db.refresh(user)
        
        # Log activity
        activity = ActivityLog(
            user_id=user.id,
            action_type="linkedin_oauth_login",
            description=f"User logged in via LinkedIn: {email}"
        )
        db.add(activity)
        db.commit()
        
        logger.info(f"User logged in via LinkedIn: {email}")
        
        return create_user_token(user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"LinkedIn OAuth failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="LinkedIn authentication failed"
        )

# --- Google OAuth ---
@router.post("/google", response_model=TokenResponse)
async def google_oauth(auth_request: OAuthCode, db: Session = Depends(get_db)):
    """Handle Google OAuth (code exchange to ID token -> user)"""
    try:
        if not settings.google_client_id or not settings.google_client_secret:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth not configured")

        token_url = "https://oauth2.googleapis.com/token"
        token_data = {
            "code": auth_request.code,
            "client_id": settings.google_client_id,
            "client_secret": settings.google_client_secret,
            "redirect_uri": settings.google_redirect_uri,
            "grant_type": "authorization_code",
        }
        token_response = requests.post(token_url, data=token_data)
        if token_response.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to exchange code for token")
        tokens = token_response.json()
        id_token = tokens.get("id_token")
        if not id_token:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing id_token from Google")

        # Get userinfo
        userinfo_resp = requests.get(
            "https://www.googleapis.com/oauth2/v3/userinfo",
            headers={"Authorization": f"Bearer {tokens.get('access_token')}"}
        )
        if userinfo_resp.status_code != 200:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to get Google userinfo")
        info = userinfo_resp.json()
        email = info.get("email")
        name = info.get("name") or (info.get("given_name", "") + " " + info.get("family_name", "")).strip()
        if not email:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google account has no email")

        user = db.query(User).filter(User.email == email).first()
        if user:
            user.is_verified = True
            user.profile_picture = info.get("picture")
        else:
            user = User(
                name=name or email.split("@")[0],
                email=email,
                subscription_plan="free",
                is_verified=True,
                profile_picture=info.get("picture"),
            )
            db.add(user)
        db.commit(); db.refresh(user)
        return create_user_token(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Google OAuth failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Google authentication failed")

# --- GitHub OAuth ---
@router.post("/github", response_model=TokenResponse)
async def github_oauth(auth_request: OAuthCode, db: Session = Depends(get_db)):
    """Handle GitHub OAuth (code -> access_token -> user)"""
    try:
        if not settings.github_client_id or not settings.github_client_secret:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GitHub OAuth not configured")
        # Exchange code for access token
        token_resp = requests.post(
            "https://github.com/login/oauth/access_token",
            headers={"Accept": "application/json"},
            data={
                "client_id": settings.github_client_id,
                "client_secret": settings.github_client_secret,
                "code": auth_request.code,
                "redirect_uri": settings.github_redirect_uri,
            },
        )
        if token_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to exchange code for token")
        access_token = token_resp.json().get("access_token")
        if not access_token:
            raise HTTPException(status_code=400, detail="Missing access_token from GitHub")

        # Fetch user
        user_resp = requests.get(
            "https://api.github.com/user",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        )
        emails_resp = requests.get(
            "https://api.github.com/user/emails",
            headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"}
        )
        if user_resp.status_code != 200 or emails_resp.status_code != 200:
            raise HTTPException(status_code=400, detail="Failed to get GitHub user")
        user_info = user_resp.json()
        emails = emails_resp.json()
        primary_email = next((e.get("email") for e in emails if e.get("primary") and e.get("verified")), None)
        email = primary_email or (emails[0].get("email") if emails else None)
        if not email:
            raise HTTPException(status_code=400, detail="GitHub account has no accessible email")
        name = user_info.get("name") or user_info.get("login")

        user = db.query(User).filter(User.email == email).first()
        if user:
            user.is_verified = True
            user.profile_picture = user_info.get("avatar_url")
        else:
            user = User(
                name=name,
                email=email,
                subscription_plan="free",
                is_verified=True,
                profile_picture=user_info.get("avatar_url"),
            )
            db.add(user)
        db.commit(); db.refresh(user)
        return create_user_token(user)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"GitHub OAuth failed: {str(e)}")
        raise HTTPException(status_code=500, detail="GitHub authentication failed")

@router.get("/linkedin/url")
async def get_linkedin_auth_url():
    """Get LinkedIn OAuth authorization URL"""
    if not settings.linkedin_client_id:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LinkedIn OAuth not configured"
        )
    
    auth_url = (
        f"https://www.linkedin.com/oauth/v2/authorization"
        f"?response_type=code"
        f"&client_id={settings.linkedin_client_id}"
        f"&redirect_uri={settings.linkedin_redirect_uri}"
        f"&state=random_string"
        f"&scope=r_liteprofile%20r_emailaddress"
    )
    
    return {"auth_url": auth_url}

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Logout user (client-side token removal)"""
    # Log activity
    activity = ActivityLog(
        user_id=current_user.id,
        action_type="user_logout",
        description=f"User logged out: {current_user.email}"
    )
    db.add(activity)
    db.commit()
    
    logger.info(f"User logged out: {current_user.email}")
    
    return {"message": "Successfully logged out"}
