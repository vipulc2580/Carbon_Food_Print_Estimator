import os
import time
from datetime import datetime, timezone
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from langchain.schema.runnable import RunnableParallel, RunnableLambda, RunnableSequence
from .schemas import DishMetrics,DishIngredients,IngredientCarbonResponse,DishCarbonAnalysisResponse,FoodItem
from .clients import LLMBuilderFactory
from .prompt_templates import (
    DISH_METRICS_SYSTEM_PROMPT,
    DISH_METRICS_USER_PROMPT,
    DISH_INGREDIENTS_SYSTEM_PROMPT,
    DISH_INGREDIENTS_USER_PROMPT,
    DISH_LCA_DATA_SYSTEM_PROMPT,
    DISH_LCA_DATA_USER_PROMPT,
    DISH_IMAGE_RECOGNITION_SYSTEM_PROMPT,
    DISH_IMAGE_RECOGNITION_USER_PROMPT
)
from src.logging.logger import global_logger
from src.db.redis_client import dish_in_cache,add_dish_carbon_foot_print_analysis
import asyncio


class LLMService:
    @staticmethod
    async def estimate_dish_metrics(dish_name: str):
        """
        Get estimated environmental impact metrics for a dish.
        Returns DishMetrics pydantic model or empty {} if invalid dish.
        """
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat()
        try:
            # --- Parser ---
            parser = PydanticOutputParser(pydantic_object=DishMetrics)
            prompt = ChatPromptTemplate.from_messages([
                ("system", DISH_METRICS_SYSTEM_PROMPT),
                ("human", DISH_METRICS_USER_PROMPT),
            ])

            # --- Get LLM client bound to parser ---
            llm = LLMBuilderFactory.get_llm_client(provider="openai")
            llm = llm.with_structured_output(DishMetrics)  # direct binding with Pydantic

            # --- Run chain ---
            chain = prompt | llm
            result = await chain.ainvoke({"dish_name": dish_name})
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            print(f"Total Time taken is {round(end_time-start_time,2)}")
            if not result or not result.model_dump(exclude_none=True):
                return None 
            return result  # already a DishMetrics object

        except Exception as e:
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            await global_logger.log_event(
                {
                    "message": "error_in_estimate_dish_metrics",
                    "error": str(e),
                    "dish_name": dish_name,
                    "start_time": start_timestamp,
                    "end_time": datetime.now(),
                    "duration_sec": duration,
                },
                level="error",
            )
            return None
    
    @staticmethod
    async def extract_dish_ingredients(dish_name: str):
        """ 
            Get List of ingredients for dish per serving.
            Returns DishIngredients pydantic model or empty {} if invalid dish.
        """
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat()
        try:
            parser = PydanticOutputParser(pydantic_object=DishIngredients)

            prompt = ChatPromptTemplate.from_messages([
                ("system", DISH_INGREDIENTS_SYSTEM_PROMPT),
                ("human", DISH_INGREDIENTS_USER_PROMPT),
            ])
            llm=LLMBuilderFactory.get_llm_client(provider="openai")
            llm=llm.with_structured_output(DishIngredients)
            
            chain = prompt | llm
            result = await chain.ainvoke({"dish_name": dish_name})
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            print(f"Total Time taken is {round(end_time-start_time,2)}")

            # handle empty {} or [] result
            if not result or not result.ingredients:
                return None

            return result  # already a DishIngredients object

        except Exception as e:
            # logging/error handling layer
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            await global_logger.log_event(
                {
                    "message": "error_extracting_ingredients",
                    "error": str(e),
                    "dish_name": dish_name,
                    "start_time": start_timestamp,
                    "end_time": datetime.now(),
                    "duration_sec": duration,
                },
                level="error",
            )
            return None
    
    @staticmethod
    async def extract_ingredient_lca(ingredients: list[str]):
        """ 
            Get estimated carbon footprint metrics for a list of ingredients.
            Returns IngredientCarbonResponse pydantic model or empty {} if invalid.
        """
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat()
        try:
            parser = PydanticOutputParser(pydantic_object=IngredientCarbonResponse)

            prompt = ChatPromptTemplate.from_messages([
                ("system", DISH_LCA_DATA_SYSTEM_PROMPT),
                ("human", DISH_LCA_DATA_USER_PROMPT),
            ])
            llm = LLMBuilderFactory.get_llm_client(provider="openai")
            llm = llm.with_structured_output(IngredientCarbonResponse)
            
            chain = prompt | llm
            result = await chain.ainvoke({"ingredients": ingredients})

            end_time = time.time()
            duration = round(end_time - start_time, 2)
            print(f"Total Time taken is {duration}")
            # handle empty {} or [] result
            if not result or not result.results:
                return None

            return result  # already an IngredientCarbonResponse object

        except Exception as e:
            # logging/error handling layer
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            await global_logger.log_event(
                {
                    "message": "error_extracting_ingredient_lca",
                    "error": str(e),
                    "ingredients": ingredients,
                    "start_time": start_timestamp,
                    "end_time": datetime.now(),
                    "duration_sec": duration,
                },
                level="error",
            )
            return None
    
    @staticmethod
    async def estimate_dish_carbon_foot_print_analysis(dish_name: str):
        """
            Takes Dish_name as input to estimate dish CarbonFootPrint analysis
        Returns dict with:
            {
                "metrics": DishMetrics,
                "ingredients": DishIngredients,
                "lca": IngredientCarbonResponse
            }
        """
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat()

        try:
            # first check in the cache 
            result=await dish_in_cache(dish_name=dish_name.lower())
            if result:
                return result
            
            metrics, ingredients = await asyncio.gather(
                LLMService.estimate_dish_metrics(dish_name),
                LLMService.extract_dish_ingredients(dish_name)
            )
            
            lca = None
            if ingredients and ingredients.ingredients:
                lca = await LLMService.extract_ingredient_lca(ingredients.ingredients)

            if not (metrics and ingredients and lca):
                return None

            duration = round(time.time() - start_time, 2)
            print(f"Total Time taken: {duration}s")
            final_result=DishCarbonAnalysisResponse(metrics=metrics, ingredients=ingredients, lca=lca)
            # store in cache 
            await add_dish_carbon_foot_print_analysis(dish_name=dish_name.lower(),value=final_result.model_dump())
            return final_result

        except Exception as e:
            duration = round(time.time() - start_time, 2)
            await global_logger.log_event(
                {
                    "message": "error_in_dish_carbon_analysis",
                    "error": str(e),
                    "dish_name": dish_name,
                    "start_time": start_timestamp,
                    "end_time": datetime.now(),
                    "duration_sec": duration,
                },
                level="error",
            )
            return None
        
        
    @staticmethod
    async def detect_dish_from_image(image_b64: str):
        """
        Detect dish/food name from an uploaded image.
        Returns DishName pydantic model with `dish_name` field.
        """
        start_time = time.time()
        start_timestamp = datetime.now(timezone.utc).isoformat()
        try:
            # --- Parser ---
            parser = PydanticOutputParser(pydantic_object=FoodItem)
            prompt = ChatPromptTemplate.from_messages([
                ("system", DISH_IMAGE_RECOGNITION_SYSTEM_PROMPT),
                ("human", [
                    {"type": "text", "text": DISH_IMAGE_RECOGNITION_USER_PROMPT},
                    {"type": "image_url", "image_url": f"data:image/jpeg;base64,{image_b64}"}
                ]),
            ])
            
            # --- Get LLM client bound to parser ---
            llm = LLMBuilderFactory.get_llm_client(provider="openai")
            llm = llm.with_structured_output(FoodItem)  # ensures proper pydantic binding

            # --- Run chain ---
            chain = prompt | llm
            result =await chain.ainvoke({})  # no text input, only image
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            print(f"Dish detection took {duration}s")
            if not result or not result.model_dump(exclude_none=True):
                return None 
            print(result)
            return result  # already DishName object

        except Exception as e:
            end_time = time.time()
            duration = round(end_time - start_time, 2)
            await global_logger.log_event(
                {
                    "message": "error_in_dish_detection",
                    "error": str(e),
                    "start_time": start_timestamp,
                    "end_time": datetime.now(),
                    "duration_sec": duration,
                },
                level="error",
            )
            return None
        
    # @staticmethod
    # async def analyze_dish_carbon_from_image(image_b64: str):
    #     """
    #     Full pipeline in one function:
    #     1. Detect dish from image
    #     2. Estimate carbon footprint
    #     Returns DishCarbonAnalysisResponse or None
    #     """
    #     try:
    #         async def detect_step(x):
    #             image_b64=x.get('image_b64')
    #             return await LLMService.detect_dish_from_image(image_b64=image_b64)

    #         async def carbon_step(detected):
    #             if not detected or not getattr(detected, "dish_name", None):
    #                 return None
    #             return await LLMService.estimate_dish_carbon_foot_print_analysis(detected.dish_name)

    #         chain = RunnableSequence(
    #             RunnableLambda(detect_step),
    #             RunnableLambda(carbon_step),
    #         )

    #         result=await chain.ainvoke({"image_b64": image_b64})
    #         return result
    #     except Exception as e:
    #         await global_logger.log_event(
    #             {
    #                 "message": "error_in_dish_carbon_from_image",
    #                 "error": str(e),
    #                 "image_b64_truncated": image_b64[:50] + "...",  # prevent logging full image
    #             },
    #             level="error",
    #         )
    #         return None
    @staticmethod
    async def analyze_dish_carbon_from_image(image_b64: str):
        """
        Full pipeline with caching:
        1. Check if dish carbon result is cached
        2. If not, detect dish from image
        3. If dish not detected → return None
        4. If detected dish is cached → return cached result
        5. Otherwise → estimate carbon + cache it
        """
        try:
            # STEP 1: Detect dish
            detected = await LLMService.detect_dish_from_image(image_b64=image_b64)
            if not detected or not getattr(detected, "dish_name", None):
                return None

            dish_name = detected.dish_name

            if not dish_name:
                return None 
            cached_dish_result=await dish_in_cache(dish_name=dish_name.lower())
            
            if cached_dish_result:
                return cached_dish_result

            # STEP 4: Estimate carbon footprint
            result = await LLMService.estimate_dish_carbon_foot_print_analysis(dish_name)
            
            return result

        except Exception as e:
            await global_logger.log_event(
                {
                    "message": "error_in_dish_carbon_from_image",
                    "error": str(e),
                    "image_b64_truncated": image_b64[:50] + "...",
                },
                level="error",
            )
            return None