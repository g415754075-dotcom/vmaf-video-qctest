"""测试配置和共享 fixture"""
import asyncio
import os
import tempfile
from pathlib import Path
from typing import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.core.database import Base, get_db
from app.core.config import settings


# 测试数据库 URL
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """创建事件循环"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="function")
async def test_db() -> AsyncGenerator[AsyncSession, None]:
    """创建测试数据库会话"""
    engine = create_async_engine(TEST_DATABASE_URL, echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(test_db: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    async def override_get_db():
        yield test_db

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.fixture
def temp_upload_dir() -> Generator[Path, None, None]:
    """创建临时上传目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        upload_path = Path(tmpdir) / "uploads"
        upload_path.mkdir(parents=True, exist_ok=True)
        yield upload_path


@pytest.fixture
def temp_reports_dir() -> Generator[Path, None, None]:
    """创建临时报告目录"""
    with tempfile.TemporaryDirectory() as tmpdir:
        reports_path = Path(tmpdir) / "reports"
        reports_path.mkdir(parents=True, exist_ok=True)
        yield reports_path


@pytest.fixture
def sample_video_content() -> bytes:
    """模拟视频文件内容"""
    # 返回简单的字节数据模拟视频
    return b"fake video content" * 1000


@pytest.fixture
def sample_chunk_data() -> bytes:
    """模拟分片数据"""
    return b"chunk data" * 100
