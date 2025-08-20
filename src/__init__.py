from fastapi import FastAPI,APIRouter,status
from fastapi.responses import JSONResponse
from src.auth.routes import auth_router
from src.estimator.routes import estimator_router
from contextlib import asynccontextmanager
from src.db.pg_sql_client import init_db
from src.utils.errors import register_error_handlers

version="v1"
    
app=FastAPI(
    title="Reewild-Carbon Food Print Estimator",
    description="A Rest API Service for Carbon Food Print Estimation",
    version=version,
    docs_url=f"/api/{version}/docs",
    contact={
        "email":"vipulc2580@gmail.com"
    }
)

main_router=APIRouter()

register_error_handlers(app)  # registering all custom error / exception handlers 

@main_router.get('/')
async def home():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message":"Welcome to Reewild-Carbon Food Print Estimation Service"
        }
    )

@main_router.get('/health')
async def health_check():
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={
            "message":"Health is OK"
        }
    )
    
app.include_router(main_router,prefix="",tags=["home"])
app.include_router(auth_router,prefix=f"/api/{version}/auth",tags=["auth"])
app.include_router(estimator_router,prefix=f"/api/{version}/estimator",tags=["estimator"])
