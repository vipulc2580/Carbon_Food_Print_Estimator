from pydantic_settings import BaseSettings,SettingsConfigDict
from pathlib import Path 

class Configuration(BaseSettings):
    DATABASE_URL:str
    JWT_SECRET:str
    JWT_ALGORITHM:str 
    LOGGER_SERVICE:str
    REDIS_URL:str
    MAIL_SERVER:str
    MAIL_PORT:int=587
    MAIL_USERNAME:str 
    MAIL_PASSWORD:str 
    MAIL_FROM:str 
    MAIL_FROM_NAME:str
    MAIL_STARTTLS:bool=True                        
    MAIL_SSL_TLS:bool=False                       
    USE_CREDENTIALS:bool=True                   
    VALIDATE_CERTS:bool=True
    DOMAIN:str 
    GOOGLE_API_KEY:str
    OPENAI_API_KEY:str
    model_config=SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent/".env",
        extra="ignore"
    )
    
Config=Configuration()

broker_url=Config.REDIS_URL
result_backend=Config.REDIS_URL
broker_connection_retry_on_startup=True