from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import timedelta
from ...core.config import settings
from ...core.security import create_access_token
from ...core.database import get_db
from ...crud.user import UserCRUD
from ...models.schemas import AuthResponse, UserCreate
from ...services.hh.client import HHClient
from ...services.redis_service import RedisService
import time
from fastapi import Request

router = APIRouter(prefix="/api/auth", tags=["auth"])

hh_client = HHClient()
redis_service = RedisService()


@router.get("/hh")
async def hh_auth(request: Request, user_id: str = None):
    """Get HH OAuth URL with token revocation"""
    access_token = None
    
    # Вариант 1: Токен из заголовков
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        access_token = auth_header[7:]
    
    # Вариант 2: Токен из cookies
    elif request.cookies.get("hh_access_token"):
        access_token = request.cookies.get("hh_access_token")
   
    # Отзываем существующий токен
    if access_token:
        revoked = await hh_client.revoke_hh_token(access_token)
        if revoked:
            pass
    
    return {
        "url": f"https://hh.ru/oauth/authorize?response_type=code&client_id={settings.HH_CLIENT_ID}&redirect_uri={settings.FRONTEND_URL}"
    }

@router.post("/callback")
async def auth_callback(code: str, db: Session = Depends(get_db)):
    """Handle OAuth callback"""
    try:
        # Exchange code for token
        token_data = await hh_client.exchange_code_for_token(code)
        
        # Get user info from HH
        user_data = await hh_client.get_user_info(token_data["access_token"])
        
        if not user_data.get('id'):
            raise HTTPException(status_code=400, detail="User ID not found")
        
        hh_user_id = str(user_data['id'])
        
        # Create or update user in DB
        user = UserCRUD.get_by_hh_id(db, hh_user_id)
        if not user:
            # Create new user
            user_create = UserCreate(
                hh_user_id=hh_user_id,
                email=user_data.get("email"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name")
            )
            user = UserCRUD.create(db, user_create)
        else:
            # Update user info
            from ...models.schemas import UserUpdate
            user_update = UserUpdate(
                email=user_data.get("email"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name")
            )
            user = UserCRUD.update(db, user.id, user_update)
        
        # Store tokens in Redis
        await redis_service.set_user_token(
            hh_user_id, 
            token_data["access_token"],
            token_data.get("expires_in", 86400)
        )
        
        if token_data.get("refresh_token"):
            await redis_service.set_refresh_token(
                hh_user_id,
                token_data["refresh_token"]
            )
        
        # Generate JWT
        jwt_token = create_access_token({"sub": hh_user_id})
        
        return AuthResponse(
            token=jwt_token,
            refresh_token=token_data.get("refresh_token"),
            user=user
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Authentication failed: {str(e)}")

@router.post("/refresh")
async def refresh_token(refresh_token: str, db: Session = Depends(get_db)):
    """Refresh access token"""
    try:
        # Get new token from HH
        token_data = await hh_client.refresh_access_token(refresh_token)
        
        # Get user info
        user_data = await hh_client.get_user_info(token_data["access_token"])
        hh_user_id = str(user_data['id'])
        
        # Get user from DB
        user = UserCRUD.get_by_hh_id(db, hh_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        # Update tokens in Redis
        await redis_service.set_user_token(
            hh_user_id, 
            token_data["access_token"],
            token_data.get("expires_in", 86400)
        )
        
        if token_data.get("refresh_token"):
            await redis_service.set_refresh_token(
                hh_user_id,
                token_data["refresh_token"]
            )
        
        # Generate new JWT
        jwt_token = create_access_token({"sub": hh_user_id})
        
        return AuthResponse(
            token=jwt_token,
            refresh_token=token_data.get("refresh_token"),
            user=user
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Token refresh failed: {str(e)}")