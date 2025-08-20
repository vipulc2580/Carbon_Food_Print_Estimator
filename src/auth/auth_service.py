from .models import User 
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select, delete
from sqlalchemy import or_
from .schemas import UserCreateModel 
from .utils import hash_password
from typing import Optional 
from src.logging.logger import global_logger
from uuid import UUID 

class AuthService:
    
    async def user_exists(self,email:str,username:str,session:AsyncSession)->bool:
        try:
            statement=select(User).where(
                or_(
                    User.email==email,
                    User.username==username
                )
            )
            result=await session.exec(statement)
            
            user=result.first()
            return True if user else False 
        except Exception as e:
            await global_logger.log_event(
                data={
                    "message":"error_fetching_user_existance",
                    "error":str(e),
                    "email":email,
                    "username":username
                },
                level="error"
            )
            raise 
        
    async def get_user_by_email(self,email:str,session:AsyncSession)->Optional[User]:
        try:
            statement=select(User).where(
                User.email==email
            )
            result=await session.exec(statement)
            user=result.first()
            
            return user if user else None 
        except Exception as e:
            await global_logger.log_event(
                data={
                    "message":"error_fetching_user_by_email",
                    "error":str(e),
                    "email":email 
                },
                level="error"
            )
            raise 
    
    async def create_user(self,user_data:UserCreateModel,session:AsyncSession):
        try:
            user_data_dict=user_data.model_dump()
            # we need pop confirm password out it 
            user_data_dict.pop('confirm_password')
            hashed_password=hash_password(user_data_dict.pop('password'))
            
            user_data_dict['hashed_password']=hashed_password
            
            user=User(**user_data_dict)
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user 
        except Exception as e:
            await session.rollback()
            await global_logger.log_event(
                data={
                    "message":"error_creating_user",
                    "error":str(e)
                },
                level="error"
            )
            raise 
            
    
    async def update_user(self,user_data:dict,session:AsyncSession)->User|None:
        try:
            email=user_data.get("email")
            user=await self.get_user_by_email(email=email,session=session)
            
            if not user:
                return None 
            
            for key,value in user_data.items():
                if value and hasattr(user,key):
                    setattr(user,key,value)
            
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user 
        except Exception as e:
            await global_logger.log_event(
                data={
                    "message":"error_occurred_updating_user",
                    "error":str(e),
                    "data":user_data
                },
                level= "error"
            )
            await session.rollback()
            raise
            
    async def delete_user(self, email: str, session: AsyncSession) -> User | None:
        try:
            statement = select(User).where(User.email == email)
            result = await session.exec(statement)
            user = result.one_or_none()

            if not user:
                return None
            
            await session.delete(user)
            await session.commit()
            return user

        except Exception as e:
            await global_logger.log_event(
                data={
                    "message": "error_occurred_deleting_user",
                    "error": str(e),
                    "email":email
                },
                level="error"
            )
            raise