from fastapi import Depends, HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.db import get_supabase

security = HTTPBearer()

def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify Supabase JWT using the Supabase client.
    
    This approach works with both the legacy HS256 JWT secret and the newer
    RS256 asymmetric signing keys, because Supabase's own client handles
    the verification internally.
    """
    token = credentials.credentials
    try:
        supabase = get_supabase()
        # Let Supabase verify the token — works with HS256 and RS256
        response = supabase.auth.get_user(token)
        if not response or not response.user:
            raise HTTPException(status_code=401, detail="Invalid or expired token")
        return response.user.id
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


def verify_organization_access(organization_id: str, user_id: str = Depends(get_current_user)):
    """Ensure the user is a member of the requested organization."""
    supabase = get_supabase()
    result = (
        supabase.table("organization_members")
        .select("id")
        .eq("organization_id", organization_id)
        .eq("user_id", user_id)
        .execute()
    )
    if not result.data:
        raise HTTPException(status_code=403, detail="Not authorized to access this organization")
    return organization_id
