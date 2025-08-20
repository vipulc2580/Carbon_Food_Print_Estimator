import redis.asyncio as redis 
from src.constants.config import Config 
from fastapi import HTTPException
from typing import Optional 
from src.logging.logger import global_logger 
from src.estimator.schemas import DishCarbonAnalysisResponse
import json 
# JWT Token id expiry time 
JTI_Expiry=3600

class RedisClient:
    """ SingleTon Class to get Redis Client"""
    _instance:Optional[redis.Redis]=None 
    
    @classmethod
    def get_instance(cls)->redis.Redis:
        if cls._instance is None:
            try:
                cls._instance=redis.from_url(Config.REDIS_URL)
            except Exception as e:
                global_logger.log_event(
                    data={
                        "message":"redis_connection_error",
                        "error":str(e),
                        "connection_str":Config.REDIS_URL
                    },
                    level="error"
                )
        return cls._instance 
    
    
async def add_jti_to_blocklist(jti:str)->None:
    """ Add JWT id to blocklist in redis"""
    client=RedisClient.get_instance()
    await client.set(name=jti,value="",ex=JTI_Expiry)

async def token_in_blocklist(jti:str)->None:
    """ Checks JWT id is present in blocklist in redis"""
    client=RedisClient.get_instance()
    value=await client.get(jti)
    return value is not None  

async def add_dish_carbon_foot_print_analysis(dish_name: str, value: dict) -> None:
    """Caching the responses for Dish Name to avoid LLM Call"""
    client = RedisClient.get_instance()
    # Serialize dict -> JSON string
    await client.set(
        name=dish_name,
        value=json.dumps(value),
        ex=JTI_Expiry
    )

async def dish_in_cache(dish_name: str) -> Optional[DishCarbonAnalysisResponse]:
    """ Checking whether dish_name exists in redis cache"""
    client = RedisClient.get_instance()
    result = await client.get(dish_name)
    if result:
        # Decode JSON string back to dict
        data = json.loads(result)
        return DishCarbonAnalysisResponse(**data)
    return None
    
    