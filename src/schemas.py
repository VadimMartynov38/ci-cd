from typing import List, Optional

from pydantic import BaseModel, Field, conint


class IngredientBase(BaseModel):
    name: str
    quantity: Optional[str]


class IngredientCreate(IngredientBase):
    pass


class Ingredient(IngredientBase):
    id: int

    class Config:
        orm_mode = True


class RecipeBase(BaseModel):
    title: str
    cook_time: int


class RecipeCreate(RecipeBase):
    ingredients: Optional[List[IngredientCreate]]


class RecipeListItem(RecipeBase):
    id: int
    views: int

    class Config:
        orm_mode = True


class Recipe(RecipeBase):
    id: int
    views: int
    ingredients: List[Ingredient]

    class Config:
        orm_mode = True
