from sqlmodel import SQLModel,Field,Column,Relationship
import sqlalchemy.dialects.postgresql as pg 
from datetime import datetime,date 
from uuid import UUID,uuid4 
from sqlalchemy import UniqueConstraint,func


""" 
Class User:
    uid
    username
    email
    first_name
    last_name
    is_verified
    hashed_password
    is_active
    is_superuser
    last_login 
    created_at
    updated_at
"""

class User(SQLModel, table=True):
    __tablename__ = "users"
    __table_args__ = (
        UniqueConstraint("email", "username", name="uq_username_email"),
    )
    uuid: UUID = Field(
        sa_column=Column(pg.UUID(as_uuid=True), primary_key=True, default=uuid4, index=True)
    )
    username: str = Field(
        sa_column=Column(pg.VARCHAR(50), nullable=False, index=True)
    )
    email: str = Field(
        sa_column=Column(pg.VARCHAR(255), nullable=False, index=True)
    )
    first_name: str = Field(
        sa_column=Column(pg.VARCHAR(100), nullable=False)
    )
    last_name: str = Field(
        sa_column=Column(pg.VARCHAR(100), nullable=False)
    )
    hashed_password: str = Field(
        sa_column=Column(pg.TEXT, nullable=False)
    )
    is_verified: bool = Field(default=False, nullable=False)
    is_active: bool = Field(default=True, nullable=False)
    is_superuser: bool = Field(default=False, nullable=False)
    last_login: datetime | None = Field(default=None)

    
    created_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), server_default=func.now(), nullable=False)
    )
    updated_at: datetime = Field(
        sa_column=Column(pg.TIMESTAMP(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    )