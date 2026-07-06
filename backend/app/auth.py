import jwt
from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.config import settings
from app.db import get_supabase

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify Supabase JWT from the Authorization header."""
    token = credentials.credentials
    try:
        # Verify JWT using Supabase JWT secret
        payload = jwt.decode(
            token, 
            settings.supabase_jwt_secret, 
            algorithms=["HS256"], 
            audience="authenticated"
        )
        return payload["sub"] # User ID
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def verify_organization_access(organization_id: str, user_id: str = Depends(get_current_user)):
    """Ensure the user is a member of the requested organization."""
    supabase = get_supabase()
    result = supabase.table("organization_members").select("id").eq("organization_id", organization_id).eq("user_id", user_id).execute()
    
    if not result.data:
        raise HTTPException(status_code=403, detail="Not authorized to access this organization")
    return organization_id
