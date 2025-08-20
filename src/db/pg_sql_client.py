from sqlmodel import create_engine,text,SQLModel
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.orm import sessionmaker 
from src.constants.config import Config
from sqlalchemy_utils import database_exists, create_database

engine=AsyncEngine(
    create_engine(
        url=Config.DATABASE_URL,
        echo=False 
    )
)

    
async def init_db():
    async with engine.begin() as conn:
        from src.auth.models import User 
        
        await conn.run_sync(SQLModel.metadata.create_all)
        
async def get_session()->AsyncSession:
    Session=sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False 
    )
    
    async with Session() as session:
        yield session