from fastapi import Query,Path,Header,Request,status,APIRouter,Depends,Response
from fastapi.exceptions import HTTPException
from fastapi.responses import JSONResponse 
from sqlmodel.ext.asyncio.session import AsyncSession
from src.db.pg_sql_client import get_session
from src.db.redis_client import add_jti_to_blocklist
from .dependencies import AccessTokenBearer,RefreshTokenBearer,UserChecker
from .schemas import UserCreateModel,UserLoginModel,EmailMixin,PasswordUpdateModel
from .auth_service import AuthService
from src.logging.logger import global_logger
from datetime import datetime,timedelta
from src.constants.config import Config 
from src.utils.celery_tasks import send_email 
from .utils import create_url_safe_token,render_template,decode_url_safe_token,verify_password,create_access_token,hash_password
from src.utils.errors import UserNotFound,InternalServerError,UserAlreadyExists,InvalidToken,CustomException,InvalidCredentials


auth_router=APIRouter()
auth_service=AuthService()
auth_checker=Depends(UserChecker())
REFRESH_TOKEN_EXPIRY=2

@auth_router.post('/signup',status_code=status.HTTP_201_CREATED)
async def signup(user_data:UserCreateModel,
                session:AsyncSession=Depends(get_session)):
    try:
        email=user_data.email 
        username=user_data.username 
        user_exists=await auth_service.user_exists(email=email,username=username,session=session)
        if user_exists:
            raise UserAlreadyExists()
        user=await auth_service.create_user(user_data=user_data,session=session)
        token=create_url_safe_token(
            {"email":email}
        )
        activation_link=f"http://{Config.DOMAIN}/api/v1/auth/verify/{token}"
        subject="Verify your email"
        html_msg=render_template('verification_email.html',activation_link=activation_link,user_name=user.username)
        send_email.delay(
            recipients=[email],
            subject=subject,
            body=html_msg
        )
        await global_logger.log_event(
            data={
                "message":"user_created_successfully",
                "user_data":str(user.model_dump()), 
                "time_stamp":datetime.now()
            },
            level="info"
        )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "message":"User account successfully created"
            }
        )
    except CustomException:
        raise
    except Exception as e:
        await global_logger.log_event(
                data={
                    "message":"error_occured_user_creation",
                    "user_data":str(user_data.model_dump()), 
                    "time_stamp":datetime.now(),
                    "error":str(e)
                },
                level="error"
            )
        raise InternalServerError()


@auth_router.get('/verify/{token}',status_code=status.HTTP_200_OK)
async def verify_user(token:str=Path(),session=Depends(get_session)):
    try:
        user_data=decode_url_safe_token(token=token)
        if not user_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid Token"
            )
        user_data['is_verified']=True 
        user_updated=await auth_service.update_user(
            user_data=user_data,
            session=session
        )
        if user_updated:
            await global_logger.log_event(
                data={
                    "message":"user_updated_successfully",
                    "token":token,
                    "user_data":user_data,
                    "timestamp":datetime.now()
                }
            )   
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message":"User updated successfully",
                    "user":user_data
                }
            )
        else:
            await global_logger.log_event(
                data={
                    "message":"error_updating_user",
                    "error":"user_not_found",
                    "token":token,
                    "user_data":user_data,
                    "timestamp":datetime.now()
                }
            )
            raise UserNotFound()
    except CustomException:
        raise
        
    except Exception as e:
        await global_logger.log_event(
            data={
                "message":"error_updating_user",
                "error":str(e),
                "token":token,
                "time_stamp":datetime.utcnow()
            }
        )
        raise InternalServerError()
        
        
@auth_router.post('/login',status_code=status.HTTP_200_OK)
async def login_user(user_data:UserLoginModel,session:AsyncSession=Depends(get_session)):
    try:    
        email=user_data.email 
        password=user_data.password 
        # get user with this email id 
        user=await auth_service.get_user_by_email(email=email,session=session)
        if not user:
            raise InvalidCredentials()
        password_matched=verify_password(plain_password=password,hashed_password=user.hashed_password)
        if not password_matched:
            raise InvalidCredentials()
        user_data_payload={
            "user_uid":str(user.uuid),
            "email":user.email,
            "is_active":user.is_active
        }
        user_updated=await auth_service.update_user(
            user_data={
                'email':user.email,
                'last_login':datetime.utcnow()
            },
            session=session
        )
        access_token=create_access_token(user_data=user_data_payload)
        refresh_token=create_access_token(user_data=user_data_payload,expiry=timedelta(days=REFRESH_TOKEN_EXPIRY),refresh=True
                                        )
        return JSONResponse(
            content={
                "message":"Logged in successfully",
                "access_token":access_token,
                "refresh_token":refresh_token,
                "user":user_data_payload
                }
        )
    except CustomException:
        raise 
    except Exception as e:
        await global_logger.log_event(
            data={
                "message":"error_occured_logging_user",
                "error":str(e),
                "user_data":str(user_data.model_dump())                
            },
            level="error"
        )
        raise InternalServerError()



@auth_router.get('/refresh-token')
async def get_new_access_token(token_details:dict=Depends(RefreshTokenBearer())):
    try:
        expiry_timestamp=token_details.get('exp')
        if datetime.fromtimestamp(expiry_timestamp) > datetime.now():
            new_access_token=create_access_token(user_data=token_details.get('user'))
            return JSONResponse(
                content={
                    "access_token":new_access_token
                }
            )
        raise InvalidToken()
    except CustomException:
        raise 
    except Exception as e:
        print(e)
        await global_logger.log_event(
            data={
                'message':"error_generating_access_token",
                "token_details":token_details,
                "error":str(e)
            }
            ,level="error"
        )
        raise InternalServerError()



@auth_router.get('/logout')
async def revoke_token(token_details:dict=Depends(AccessTokenBearer())):
    try:
        jti=token_details.get('jti','')
        await add_jti_to_blocklist(jti=jti)
        
        return JSONResponse(status_code=status.HTTP_200_OK,content={
            "message":"Logged Out Successfully"
        })
    except Exception as e:
        await global_logger.log_event(
            data={
                "message":"error_occured_logout_user",
                "error":str(e),
                "time_stamp":datetime.utcnow(),
                "token_detail":str(token_details)
            },
            level="error"
        )
        raise InternalServerError()
    
@auth_router.post('/password-reset-request',status_code=status.HTTP_200_OK)
async def password_reset_request(email_data:EmailMixin,session=Depends(get_session)):
    try:
        current_user=await auth_service.get_user_by_email(email=email_data.email,session=session)
        if not current_user:
            raise UserNotFound()
        
        token=create_url_safe_token(data={"email":email_data.email})
        
        password_reset_link=f"http://{Config.DOMAIN}/api/v1/auth/password-reset-confirm/{token}"
        
        subject="Please reset your Password"
        html_msg=render_template('password_reset.html',
                                user_name=current_user.username,
                                password_reset_link=password_reset_link
                                ,current_year=datetime.now().year)
        send_email.delay(
            recipients=[email_data.email],
            subject=subject,
            body=html_msg
        )
        await global_logger.log_event(
            data={
                "message":"password_reset_request_successfully",
                "user":current_user.model_dump(),
                "time_stamp":datetime.utcnow()
            }
        )
        return JSONResponse(
            content={
                "message": "Please check your email for instructions to reset your password",
            },
            status_code=status.HTTP_200_OK,
        )
    except CustomException:
        raise 
    except Exception as e:
        await global_logger.log_event(
            data={
                "message":"error_occurred_password_reset_request",
                "error":str(e),
                "time_stamp":datetime.utcnow(),
                "email_data":email_data.email 
            },
            level="error"
        )
        raise InternalServerError()
        
        
@auth_router.post('/password-reset-confirm/{token}')
async def password_reset_confirm(password_update_data:PasswordUpdateModel,token:str=Path(),session:AsyncSession=Depends(get_session)):
    try:
        # first check whether new password is same as old if yes return error saying new password 
        # can't be same as previous one 
        token_data=decode_url_safe_token(token=token)
        if not token_data:
            raise InvalidToken()
        email=token_data.get('email','')
        current_user=await auth_service.get_user_by_email(email=email,session=session)
        if not current_user:
            raise UserNotFound()
        
        new_password_match=verify_password(plain_password=password_update_data.password,hashed_password=current_user.hashed_password)
        if new_password_match:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "message":"New Password is same as old",
                    "error":"new_password_is_equal_to_oldpassword",
                    "resolution":"Please provide new password different than previous password"
                }
            )
        new_password_hash=hash_password(password=password_update_data.password)
        await auth_service.update_user({
            "hashed_password":new_password_hash,
            "email":current_user.email
        },
        session=session)
        return JSONResponse(
            content={"message": "Password reset Successfully"},
            status_code=status.HTTP_200_OK,
        )
    except CustomException:
        raise
    except Exception as e:
        await global_logger.log_event(
                data={
                    "message":"error_occured_deleting_user",
                    "error":str(e),
                    "time_stamp":datetime.utcnow(),
                    "token_detail":token,
                    "password_details":str(password_update_data.model_dump())
                },
                level="error"
            )
        raise InternalServerError()
        
@auth_router.post('/delete-account',dependencies=[auth_checker])
async def delete_account(token_details:dict=Depends(AccessTokenBearer()),session:AsyncSession=Depends(get_session)):
    try:
        user_data=token_details.get('user',{})
        email=user_data.get('email','')
        current_user=await auth_service.get_user_by_email(email=email,session=session)
        if not current_user:
            raise UserNotFound()
        
        user=await auth_service.delete_user(email=email,session=session)
        if user:
            await global_logger.log_event(
                data={
                    "message":"user_account_deleted_successfully",
                    "email":email,
                    "timestamp":datetime.utcnow(),
                    "token_details":str(token_details),
                    "user_details":str(user.model_dump())
                },
                level="info"
            )
            return Response(status_code=status.HTTP_204_NO_CONTENT)
        else:
            raise UserNotFound()
    except CustomException:
        raise 
    except Exception as e:
        await global_logger.log_event(
            data={
                "message":"error_occured_deleting_user",
                "error":str(e),
                "time_stamp":datetime.utcnow(),
                "token_detail":str(token_details)
            }
            ,level="error"
        )
        raise InternalServerError()
            