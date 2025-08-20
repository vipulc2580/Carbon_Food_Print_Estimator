from passlib.context import CryptContext
from datetime import datetime,timedelta 
from src.constants.config import Config 
from itsdangerous import URLSafeTimedSerializer,SignatureExpired, BadSignature
from src.logging.logger import global_logger
from jinja2 import Environment,FileSystemLoader
from pathlib import Path 
import jwt
import uuid 

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ACCESS_TOKEN_EXPIRY=3600
# Path to templates folder 
TEMPLATES_DIR=Path(__file__).resolve().parent.parent/"templates"


env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))

serializer = URLSafeTimedSerializer(Config.JWT_SECRET,salt="email-configuration")

def hash_password(password: str) -> str:
    """ Generate Hash for given password"""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """ verify the plain password with given hash of stored password"""
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(user_data:dict,expiry:timedelta=None,refresh:bool=False):
    # this function is going to create both access and refresh token (ideally refresh token is more longed)
    # (lived and can be used to generate new access token if refresh token is valid) else we need logout and re
    # - login again 
    payload={
        "user":user_data,
        "exp":datetime.now()+(expiry if expiry else timedelta(seconds=ACCESS_TOKEN_EXPIRY)),
        "jti":str(uuid.uuid4()),
        "refresh":refresh
    }
    
    token=jwt.encode(
        payload=payload,
        key=Config.JWT_SECRET,
        algorithm=Config.JWT_ALGORITHM
    )
    return token 

def verify_token(token:str)->dict:
    # since the token is invalid or token is expired jwt might raise an error to avoid it 
    try:
        token_data=jwt.decode(jwt=token,
                        key=Config.JWT_SECRET,
                    algorithms=Config.JWT_ALGORITHM)
        return token_data 
    except jwt.PyJWTError as e:
        return None 
    
def create_url_safe_token(data:dict):
    """ Creates encoded token for given data"""
    token=serializer.dumps(data)
    
    return token 

def decode_url_safe_token(token:str):
    """ Decodes the token details from given encoded token"""
    try:
        token_data = serializer.loads(token, max_age=300)  # token valid only for 5 mins
        return token_data
    except Exception as e:
        return None 

def render_template(template_name: str, **kwargs) -> str:
    """Render Jinja2 template with given context"""
    try:
        template = env.get_template(template_name)
        return template.render(**kwargs)
    except Exception as e:
        global_logger.log_event(
            data={
                "message":"error_rendering_jinja_template",
                "error":str(e),
                "template_name":template_name
            }
        )