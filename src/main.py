from typing import List

from fastapi import FastAPI, HTTPException
from sqlalchemy import asc, desc
from sqlalchemy.future import select
from starlette import status

import models
import schemas
from database import engine, session

app = FastAPI()


@app.on_event("startup")
async def shutdown():
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)


@app.on_event("shutdown")
async def shutdown():
    await session.close()
    await engine.dispose()


@app.post(
    "/recipes", response_model=schemas.Recipe, status_code=status.HTTP_201_CREATED
)
async def create_recipe(payload: schemas.RecipeCreate):
    new = models.Recipe(title=payload.title, cook_time=payload.cook_time)
    if payload.ingredients:
        for ing in payload.ingredients:
            new.ingredients.append(
                models.Ingredient(name=ing.name, quantity=ing.quantity)
            )
    session.add(new)
    await session.commit()
    await session.refresh(new)
    return new


@app.get("/recipes", response_model=List[schemas.RecipeListItem])
async def list_recipes() -> List[models.Recipe]:
    res = await session.execute(
        select(models.Recipe).order_by(
            desc(models.Recipe.views), asc(models.Recipe.cook_time)
        )
    )
    return res.scalars().all()


@app.get("/recipes/{recipe_id}", response_model=schemas.Recipe)
async def get_recipe(recipe_id: int) -> models.Recipe:
    q = select(models.Recipe).where(models.Recipe.id == recipe_id)
    res = await session.execute(q)
    recipe = res.scalars().first()
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    recipe.views += 1
    session.add(recipe)
    await session.commit()
    await session.refresh(recipe)
    return recipe
