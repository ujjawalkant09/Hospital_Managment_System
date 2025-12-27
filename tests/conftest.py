import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession,async_sessionmaker
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool


from app.database import Base, get_db
from app.main import app

TEST_DATABASE_URL = "postgresql+asyncpg://QA_Test:QA_Test@localhost:5433/HMS_TEST"


@pytest_asyncio.fixture(scope="session")
async def test_engine():
    engine = create_async_engine(
        TEST_DATABASE_URL,
        poolclass=NullPool,
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture
async def override_get_db(test_engine):
    async_session = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async def _get_db():
        async with async_session() as session:
            yield session

    app.dependency_overrides[get_db] = _get_db

    async with async_session() as session:
        yield session

    app.dependency_overrides.clear()


@pytest.fixture
async def test_session(test_engine):
    async_session = async_sessionmaker(
        test_engine,
        expire_on_commit=False,
        class_=AsyncSession,
    )

    async with async_session() as session:
        yield session
        await session.rollback()