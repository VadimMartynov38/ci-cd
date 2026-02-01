import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

import src.main as main_module
from src import models
import src.database as database_module

app = main_module.app
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)
    TestSessionLocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)

    monkeypatch.setattr(main_module, "engine", engine)
    monkeypatch.setattr(main_module, "session", TestSessionLocal)

    monkeypatch.setattr(database_module, "engine", engine)
    monkeypatch.setattr(database_module, "session", TestSessionLocal)

    models.Base.metadata.drop_all(bind=engine.sync_engine, checkfirst=True)

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
    await engine.dispose()

@pytest.mark.asyncio
async def test_create_and_get_recipe():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        payload = {
            "title": "Soup",
            "cook_time": 15,
            "ingredients": [{"name": "Water", "quantity": "1L"}]
        }
        r = await ac.post("/recipes", json=payload)
        assert r.status_code == 201
        data = r.json()
        assert data["title"] == "Soup"
        assert data["cook_time"] == 15
        assert data["views"] == 0
        assert len(data["ingredients"]) == 1
        rid = data["id"]

        r2 = await ac.get(f"/recipes/{rid}")
        assert r2.status_code == 200
        assert r2.json()["views"] == 1

        r3 = await ac.get(f"/recipes/{rid}")
        assert r3.status_code == 200
        assert r3.json()["views"] == 2

@pytest.mark.asyncio
async def test_list_ordering_and_multiple():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        ps = [
            {"title": "A", "cook_time": 5, "ingredients": []},
            {"title": "B", "cook_time": 3, "ingredients": []},
            {"title": "C", "cook_time": 7, "ingredients": []},
        ]
        ids = []
        for p in ps:
            r = await ac.post("/recipes", json=p)
            assert r.status_code == 201
            ids.append(r.json()["id"])

        await ac.get(f"/recipes/{ids[1]}")
        await ac.get(f"/recipes/{ids[1]}")
        await ac.get(f"/recipes/{ids[2]}")

        r = await ac.get("/recipes")
        assert r.status_code == 200
        titles = [item["title"] for item in r.json()]
        assert titles[0] == "B"
        assert titles[1] == "C"
        assert titles[2] == "A"

@pytest.mark.asyncio
async def test_get_nonexistent():
    async with AsyncClient(app=app, base_url="http://testserver") as ac:
        r = await ac.get("/recipes/9999")
        assert r.status_code == 404
        assert r.json()["detail"] == "Recipe not found"