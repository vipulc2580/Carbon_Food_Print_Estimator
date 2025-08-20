from pydantic import BaseModel, Field
from typing import Optional,List,Literal

class FoodItem(BaseModel):
    dish_name:str

class DishMetrics(BaseModel):
    dish: Optional[str] = Field(
        None, description="The name of the dish, e.g., 'Chicken Biryani'"
    )
    estimated_carbon_kg: Optional[float] = Field(
        None, description="Total CO2e emissions (kg) for one serving of the dish"
    )
    serving_size_g: Optional[float] = Field(
        None, description="Typical serving size of the dish in grams"
    )
    estimation_accuracy: Optional[float] = Field(
        None, description="Confidence in the estimate, expressed as percentage (0-100)"
    )
    impact_rating: Optional[str] = Field(
        None,
        description="Impact rating from A (very low) to E (very high) based on carbon footprint",
        pattern="^[A-E]$"
    )
    carbon_per_serving_kg: Optional[float] = Field(
        None, description="Carbon footprint (kg CO2e) per serving; same as estimated_carbon_kg"
    )
    ingredient_count: Optional[int] = Field(
        None, description="Approximate number of ingredients in the dish"
    )
    car_miles_equivalent: Optional[float] = Field(
        None, description="Equivalent miles driven in a petrol car"
    )

class Ingredient(BaseModel):
    ingredient_name: str = Field(..., description="Name of the ingredient in lowercase")
    ingredient_weight_kg: float = Field(..., description="Weight of the ingredient in kilograms")


class DishIngredients(BaseModel):
    dish: str = Field(..., description="Dish name provided by the user")
    ingredients: List[Ingredient] = Field(..., description="List of main ingredients with estimated weights")
    
class IngredientCarbonFootprint(BaseModel):
    ingredient_name: str = Field(
        ...,
        description="The raw ingredient name provided by the user input (e.g., 'Mozzarella cheese')."
    )
    matched_ingredient: str = Field(
        ...,
        description="Canonical ingredient name matched from the Life Cycle Assessment (LCA) dataset."
    )
    carbon_footprint_kg_co2e: float = Field(
        ...,
        description="Total estimated carbon footprint (kg CO2e) of the ingredient across its entire life cycle."
    )
    farming_footprint_kg_co2e: float = Field(
        ...,
        description="Estimated CO2e emissions (kg) from farming and cultivation of the ingredient."
    )
    packaging_footprint_kg_co2e: float = Field(
        ...,
        description="Estimated CO2e emissions (kg) from packaging processes of the ingredient."
    )
    processing_footprint_kg_co2e: float = Field(
        ...,
        description="Estimated CO2e emissions (kg) from industrial/food processing activities applied to the ingredient."
    )
    retail_footprint_kg_co2e: float = Field(
        ...,
        description="Estimated CO2e emissions (kg) from storage, refrigeration, and display of the ingredient in retail."
    )
    transportation_footprint_kg_co2e: float = Field(
        ...,
        description="Estimated CO2e emissions (kg) from transportation and logistics of the ingredient across the supply chain."
    )
    match_confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confidence score (0 to 1) indicating how accurately the ingredient was matched to the LCA dataset."
    )
    matched: bool = Field(
        ...,
        description="Indicates whether the ingredient could be successfully matched to an entry in the LCA dataset."
    )
    lca_source: str = Field(
        ...,
        description="The source dataset used for LCA data (e.g., 'Foodsteps', 'Poore & Nemecek 2018')."
    )
    
class IngredientCarbonResponse(BaseModel):
    results: List[IngredientCarbonFootprint]

class DishCarbonAnalysisResponse(BaseModel):
    metrics: DishMetrics
    ingredients: DishIngredients
    lca: IngredientCarbonResponse
    


class ValidatedImage(BaseModel):
    filename: str
    size_bytes: int = Field(..., description="Image size in bytes")
    content_type: Literal["image/png", "image/jpeg", "image/jpg", "image/webp"]
    image_b64:str 

