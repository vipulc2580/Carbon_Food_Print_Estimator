from typing import Any,Callable 
from fastapi import FastAPI,status
from fastapi.requests import Request
from fastapi.responses import JSONResponse 

class CustomException(Exception):
    """
        This is Base Class for all CustomException/Error in Bookly
    Args:
        Exception (_type_): _description_
    """
    pass 

class InvalidToken(CustomException):
    """
        This is Invalid Token Exception to raised when Invalid Token/Expired Token 
        isCustomException
        Exception (_type_): _description_
    """
    pass 

class RevokedToken(CustomException):
    """User has provided a token that has been revoked"""
    pass

class AccessTokenRequired(CustomException):
    """User has provided a refresh token when an access token is needed"""
    pass

class RefreshTokenRequired(CustomException):
    """User has provided an access token when a refresh token is needed"""
    pass

class UserAlreadyExists(CustomException):
    """User has provided an email for a user who exists during sign up."""
    pass

class InvalidCredentials(CustomException):
    """User has provided wrong email or password during log in."""
    pass

class InsufficientPermission(CustomException):
    """User does not have the necessary permissions to perform an action."""
    pass

class UserNotFound(CustomException):
    """User Not found"""
    pass

class AccountNotVerified(CustomException):
    """User Account is not verified"""
    pass 

class AccountIsInactive(CustomException):
    """ User Account is inactive"""
    pass 

class InternalServerError(CustomException):
    """ Internal Server Error Occurred"""
    pass 

def create_exception_handler(status_code:int,data:Any)->Callable[[Request,Exception],JSONResponse]:
    """ this will return error handler function """
    async def exception_handler(request:Request,exc:CustomException)->JSONResponse:
        return JSONResponse(status_code=status_code,content=data)
    
    return exception_handler





... # rest of the file
def register_error_handlers(app: FastAPI):
    app.add_exception_handler(
        UserAlreadyExists,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            data={
                "message": "User with email already exists",
                "error_code": "user_exists",
            },
        ),
    )

    app.add_exception_handler(
        UserNotFound,
        create_exception_handler(
            status_code=status.HTTP_404_NOT_FOUND,
            data={
                "message": "User not found",
                "error_code": "user_not_found",
            },
        ),
    )
    
    app.add_exception_handler(
        InvalidCredentials,
        create_exception_handler(
            status_code=status.HTTP_400_BAD_REQUEST,
            data={
                "message": "Invalid Email Or Password",
                "error_code": "invalid_email_or_password",
            },
        ),
    )
    app.add_exception_handler(
        InvalidToken,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": "Token is invalid Or expired",
                "resolution": "Please get new token",
                "error_code": "invalid_token",
            },
        ),
    )
    app.add_exception_handler(
        RevokedToken,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": "Token is invalid or has been revoked",
                "resolution": "Please get new token",
                "error_code": "token_revoked",
            },
        ),
    )
    app.add_exception_handler(
        AccessTokenRequired,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": "Please provide a valid access token",
                "resolution": "Please get an access token",
                "error_code": "access_token_required",
            },
        ),
    )
    app.add_exception_handler(
        RefreshTokenRequired,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            data={
                "message": "Please provide a valid refresh token",
                "resolution": "Please get an refresh token",
                "error_code": "refresh_token_required",
            },
        ),
    )
    app.add_exception_handler(
        InsufficientPermission,
        create_exception_handler(
            status_code=status.HTTP_401_UNAUTHORIZED,
            data={
                "message": "You do not have enough permissions to perform this action",
                "error_code": "insufficient_permissions",
            },
        ),
    )
    

    app.add_exception_handler(
        AccountNotVerified,
        create_exception_handler(
        status_code=status.HTTP_403_FORBIDDEN,
        data={
            "message":"Account not verified",
            "error_code":"account not verified",
            "resolution":"Please check your email for verification details"
        }
        )
    )
    
    app.add_exception_handler(
        AccountIsInactive,
        create_exception_handler(
            status_code=status.HTTP_403_FORBIDDEN,
            data={
                "message":"Account not Active",
                "error_code":"account not active / deleted",
            }
        )
    )
    app.add_exception_handler(
        InternalServerError,
        create_exception_handler(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            data={
                "error":"Oops! Error occurred",
            }
        )
    )
    # @app.exception_handler(500)
    # async def internal_server_error(request, exc):

    #     return JSONResponse(
    #         content={
    #             "message": "Oops! Something went wrong",
    #             "error_code": "server_error",
    #         },
    #         status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
    #     )