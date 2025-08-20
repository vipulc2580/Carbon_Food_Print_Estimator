from fastapi import Query,Path,Header,Request,status,APIRouter,Depends
from .llm_service import LLMService
from fastapi.responses import JSONResponse 
from src.logging.logger import global_logger
from src.utils.errors import InternalServerError
from .schemas import ValidatedImage 
from .utils import validate_image 


estimator_router=APIRouter()


@estimator_router.post('/estimate')
async def estimate_dish_carbon_foot_print(dish:str): 
    try:
        print(dish)
        # ingredients=[
        #     "paneer",
        #     "butter",
        #     "tomato",
        #     "cream",
        #     "spices",
        #     "chicken",
        #     "rice",
        #     "lentils",
        #     "potato",
        #     "onion",
        #     "garlic",
        #     "ginger",
        #     "oil",
        #     "wheat flour",
        #     "sugar"
        # ]
        result=await LLMService.estimate_dish_carbon_foot_print_analysis(dish_name=dish)
        if not result:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message":"Invalid Dish Name provided",
                }
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "dish_metrics":result.model_dump()
            }
        )
    except Exception as e:
        await global_logger.log_event(
            data={
                "message":"error_occured_extracting_dish_metrics",
                "error":str(e),
            },
            level="info"
        )
        raise InternalServerError()
        
        
@estimator_router.post('/estimate/image')
async def estimate_image_dish_carbon_foot_print(valid_image: ValidatedImage = Depends(validate_image)):
    # We can now save file to storage (S3, GCS, local, etc.)
    
    image_url = f"https://cdn.example.com/{valid_image.filename}"
    
    image_data={
        "image_url": image_url,
        "size_bytes": valid_image.size_bytes,
        "content_type": valid_image.content_type,
        "image_b64":valid_image.image_b64
    }
    try:
        result=await LLMService.analyze_dish_carbon_from_image(image_b64=valid_image.image_b64)
        if not result:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={
                    "message":"No Food Item/Dish Detected in Image"
                }
            )
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "dish_metrics":result.model_dump()
            }
        )
    except Exception as e:
        raise InternalServerError()