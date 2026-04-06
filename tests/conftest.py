"""
测试配置和共享 Fixtures
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys
from pathlib import Path

# 添加 backend 到路径
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

from app.models.database import Base, get_db

# 使用内存数据库进行测试
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建测试数据库表
Base.metadata.create_all(bind=engine)


def override_get_db():
    """覆盖数据库依赖"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client():
    """创建测试客户端 - 使用 httpx 直接请求"""
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from starlette.testclient import TestClient
    from app.api import api_router
    
    # 创建测试专用的 FastAPI 应用（不使用 lifespan）
    test_app = FastAPI(
        title="AI论文小助手 API (Test)",
        description="测试环境",
        version="1.0.0"
    )
    
    # 配置CORS
    test_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # 注册API路由
    test_app.include_router(api_router)
    
    # 覆盖数据库依赖
    test_app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(test_app) as test_client:
        yield test_client


@pytest.fixture(scope="function")
def auth_client(client):
    """创建已认证的测试客户端"""
    # 注册测试用户
    client.post("/api/auth/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123"
    })
    
    # 登录获取token
    response = client.post("/api/auth/login", json={
        "username": "testuser",
        "password": "testpass123"
    })
    
    data = response.json()
    if data.get("code") == 200:
        token = data["data"]["access_token"]
        # 设置默认headers
        client.headers = {"Authorization": f"Bearer {token}"}
    
    return client
