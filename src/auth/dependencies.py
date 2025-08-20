from fastapi.security import HTTPBearer
from fastapi import Request,status,Depends
from fastapi.exceptions import HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials
from .utils import verify_token 
from .auth_service import AuthService
from .schemas import UserModel 
from sqlmodel.ext.asyncio.session import AsyncSession 
from src.db.pg_sql_client import get_session
from src.db.redis_client import token_in_blocklist
from src.logging.logger import global_logger 
from src.utils.errors import InvalidToken,AccountNotVerified,AccountIsInactive
from typing import Any 


auth_service=AuthService()

class TokenBearer(HTTPBearer):
    
    def __init__(self,auto_error=True):
        super().__init__(auto_error=auto_error)
    
    async def __call__(self,request:Request)->HTTPAuthorizationCredentials:
        try:
            creds=await super().__call__(request)
            
            token=creds.credentials
            
            if not self.token_valid(token=token):
                raise InvalidToken()
            
            token_data=verify_token(token=token)
            if await token_in_blocklist(token_data.get('jti','')):
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,
                                    detail={
                                        "error":"This token is invalid or been revoked",
                                        "resolution":"Please get new token"
                                    })
            self.verify_token_data(token_data=token_data)
            return token_data
        except Exception as e:
            await global_logger.log_event(
                data={
                    "message":"error_in_extracting_token_bearer",
                    "error":str(e)
                },
                level="error"
            )
    
    def token_valid(self,token:str)->bool:
        token_data=verify_token(token)
        return True if token_data else False 
        
    
    def verify_token_data(self,token_data:dict)->None:
        raise NotImplementedError('Please Override this method in Child class')
    
class AccessTokenBearer(TokenBearer):
    
    def verify_token_data(self,token_data:dict)->None:
        if token_data and token_data.get('refresh'):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Please provide a valid access token")
        

class RefreshTokenBearer(TokenBearer):
    
    def verify_token_data(self,token_data:dict)->None:
        if token_data and not token_data.get('refresh'):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail="Please provide a valid refresh token")

async def get_current_user(token_details:dict=Depends(AccessTokenBearer()),session:AsyncSession=Depends(get_session)):
    user_email=token_details.get('user',{}).get('email')
    
    user=await auth_service.get_user_by_email(email=user_email,session=session)
    return user

class UserChecker:
    
    def __call__(self,current_user:UserModel=Depends(get_current_user))->Any:
        if not current_user.is_verified:
            raise AccountNotVerified()
        
        if not current_user.is_active:
            raise AccountIsInactive()
            
        return True 