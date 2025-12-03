from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.user import User
from app.models.job import RecommendedJob
from app.utils.auth import get_current_active_user
from app.config import settings
from app.utils.logger import get_logger
from urllib.parse import quote
import requests
import json

router = APIRouter()
logger = get_logger(__name__)

@router.get("/login")
def linkedin_login():
    """Generate LinkedIn OAuth login URL"""
    try:
        if not settings.linkedin_client_id:
            raise HTTPException(status_code=500, detail="LinkedIn client ID not configured")
        
        # LinkedIn requires redirect_uri to match exactly; ensure it is URL-encoded in the auth URL
        encoded_redirect = quote(settings.linkedin_redirect_uri, safe='')
        url = (
            "https://www.linkedin.com/oauth/v2/authorization"
            f"?response_type=code&client_id={settings.linkedin_client_id}"
            f"&redirect_uri={encoded_redirect}"
            "&scope=openid%20profile%20email"  # OpenID Connect scopes
            "&state=random_state_string"  # Add state for security
        )
        return {"auth_url": url}
    except Exception as e:
        logger.error(f"Failed to generate LinkedIn login URL: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to generate login URL")

@router.get("/callback")
def linkedin_callback(code: str, state: str = None, db: Session = Depends(get_db)):
    """Handle LinkedIn OAuth callback"""
    try:
        if not settings.linkedin_client_secret:
            raise HTTPException(status_code=500, detail="LinkedIn client secret not configured")
        
        # Exchange code for access token
        token_url = "https://www.linkedin.com/oauth/v2/accessToken"
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": settings.linkedin_redirect_uri,
            "client_id": settings.linkedin_client_id,
            "client_secret": settings.linkedin_client_secret,
        }
        
        response = requests.post(
            token_url, 
            data=data, 
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            logger.error(f"LinkedIn token exchange failed: {response.text}")
            raise HTTPException(status_code=400, detail="LinkedIn token exchange failed")
        
        token_data = response.json()
        access_token = token_data.get("access_token")
        
        if not access_token:
            raise HTTPException(status_code=400, detail="No access token received")
        
        # Get user profile from LinkedIn using OpenID Connect
        profile_url = "https://api.linkedin.com/v2/userinfo"
        headers = {"Authorization": f"Bearer {access_token}"}
        
        profile_response = requests.get(profile_url, headers=headers)
        if profile_response.status_code != 200:
            logger.error(f"Failed to get LinkedIn profile: {profile_response.text}")
            raise HTTPException(status_code=400, detail="Failed to get LinkedIn profile")
        
        profile_data = profile_response.json()
        linkedin_id = profile_data.get("sub")  # OpenID Connect uses 'sub' for subject ID
        
        # Find or create user - prioritize updating existing dev user (ID 1)
        user = db.query(User).filter(User.id == 1).first()  # Get dev user first
        
        if not user:
            # If no dev user exists, find by LinkedIn ID
            user = db.query(User).filter(User.linkedin_id == linkedin_id).first()
        
        if not user:
            # Create new user
            user = User(
                linkedin_id=linkedin_id,
                name=profile_data.get("name", ""),
                email=profile_data.get("email", f"{linkedin_id}@linkedin.com"),
                linkedin_access_token=access_token,
                is_active=True,
                is_verified=True
            )
            db.add(user)
        else:
            # Clear LinkedIn ID from any other user first to avoid constraint violation
            db.query(User).filter(User.linkedin_id == linkedin_id).update({
                "linkedin_id": None,
                "linkedin_access_token": None
            })
            
            # Update existing user's LinkedIn info
            user.linkedin_id = linkedin_id
            user.linkedin_access_token = access_token
            user.is_verified = True
            if not user.name:
                user.name = profile_data.get("name", "")
            if not user.email or user.email.endswith("@linkedin.com"):
                user.email = profile_data.get("email", f"{linkedin_id}@linkedin.com")
        
        db.commit()
        db.refresh(user)
        
        logger.info(f"LinkedIn authentication successful for user {user.id}")
        
        # Redirect back to frontend with success message
        frontend_url = "http://localhost:8080/recommended-jobs?linkedin=connected"
        
        # Create HTML page that closes popup and notifies parent
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LinkedIn Connection Successful</title>
            <style>
                body {{
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}
                .container {{
                    text-align: center;
                    background: rgba(255, 255, 255, 0.1);
                    padding: 40px;
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
                }}
                .success-icon {{
                    font-size: 4rem;
                    margin-bottom: 20px;
                }}
                h1 {{
                    margin: 0 0 10px 0;
                    font-size: 2rem;
                }}
                p {{
                    margin: 0 0 20px 0;
                    opacity: 0.9;
                }}
                .spinner {{
                    border: 3px solid rgba(255, 255, 255, 0.3);
                    border-radius: 50%;
                    border-top: 3px solid white;
                    width: 30px;
                    height: 30px;
                    animation: spin 1s linear infinite;
                    margin: 20px auto;
                }}
                @keyframes spin {{
                    0% {{ transform: rotate(0deg); }}
                    100% {{ transform: rotate(360deg); }}
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✅</div>
                <h1>LinkedIn Connected!</h1>
                <p>Your LinkedIn account has been successfully connected to JobAlign AI.</p>
                <p>You can now get personalized job recommendations!</p>
                <div class="spinner"></div>
                <p style="font-size: 0.9rem; opacity: 0.7;">This window will close automatically...</p>
            </div>
            <script>
                // Notify parent window
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'LINKEDIN_CONNECTED',
                        success: true,
                        message: 'LinkedIn account connected successfully!'
                    }}, '*');
                }}
                
                // Close popup after showing success message
                setTimeout(() => {{
                    window.close();
                }}, 2000);
                
                // Fallback: redirect if popup doesn't close
                setTimeout(() => {{
                    window.location.href = '{frontend_url}';
                }}, 3000);
            </script>
        </body>
        </html>
        """
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
        
    except HTTPException as e:
        logger.error(f"LinkedIn callback HTTP error: {str(e)}")
        frontend_url = f"http://localhost:8080/recommended-jobs?linkedin=error&message={str(e.detail)}"
        
        # Create HTML page for error that closes popup
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LinkedIn Connection Error</title>
        </head>
        <body>
            <script>
                // Notify parent window of error
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'LINKEDIN_ERROR',
                        error: '{str(e.detail)}'
                    }}, '*');
                }}
                
                // Close popup
                window.close();
                
                // Fallback: redirect if popup doesn't close
                setTimeout(() => {{
                    window.location.href = '{frontend_url}';
                }}, 1000);
            </script>
            <p>LinkedIn connection failed: {str(e.detail)}</p>
        </body>
        </html>
        """
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
    except Exception as e:
        logger.error(f"LinkedIn callback failed: {str(e)}")
        frontend_url = f"http://localhost:8080/recommended-jobs?linkedin=error&message=Authentication failed"
        
        # Create HTML page for error that closes popup
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>LinkedIn Connection Error</title>
        </head>
        <body>
            <script>
                // Notify parent window of error
                if (window.opener) {{
                    window.opener.postMessage({{
                        type: 'LINKEDIN_ERROR',
                        error: 'Authentication failed'
                    }}, '*');
                }}
                
                // Close popup
                window.close();
                
                // Fallback: redirect if popup doesn't close
                setTimeout(() => {{
                    window.location.href = '{frontend_url}';
                }}, 1000);
            </script>
            <p>LinkedIn connection failed: Authentication failed</p>
        </body>
        </html>
        """
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)

@router.post("/disconnect")
def disconnect_linkedin(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """Disconnect LinkedIn account"""
    try:
        current_user.linkedin_access_token = None
        current_user.linkedin_id = None
        db.commit()
        
        logger.info(f"LinkedIn disconnected for user {current_user.id}")
        
        return {"message": "LinkedIn disconnected successfully"}
        
    except Exception as e:
        logger.error(f"Failed to disconnect LinkedIn: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to disconnect LinkedIn")

@router.get("/status")
def linkedin_status(current_user: User = Depends(get_current_active_user)):
    """Check LinkedIn connection status"""
    return {
        "connected": bool(current_user.linkedin_access_token),
        "linkedin_id": current_user.linkedin_id
    }