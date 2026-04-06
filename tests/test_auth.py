"""
认证模块单元测试
"""
import pytest
import uuid


class TestAuth:
    """认证接口测试"""
    
    def get_unique_username(self):
        """生成唯一用户名"""
        return f"user_{str(uuid.uuid4())[:8]}"
    
    def test_register_success(self, client):
        """测试正常注册"""
        username = self.get_unique_username()
        response = client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "id" in data["data"]
    
    def test_register_duplicate_username(self, client):
        """测试重复用户名"""
        username = self.get_unique_username()
        
        # 先注册一个
        client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}_1@example.com",
            "password": "testpass123"
        })
        
        # 再注册相同的
        response = client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}_2@example.com",
            "password": "testpass123"
        })
        assert response.status_code == 400
    
    def test_login_success(self, client):
        """测试正常登录"""
        username = self.get_unique_username()
        
        # 先注册
        client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "testpass123"
        })
        
        # 登录
        response = client.post("/api/auth/login", json={
            "username": username,
            "password": "testpass123"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "access_token" in data["data"]
        assert "user" in data["data"]
    
    def test_login_wrong_password(self, client):
        """测试错误密码"""
        username = self.get_unique_username()
        
        # 先注册
        client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "testpass123"
        })
        
        response = client.post("/api/auth/login", json={
            "username": username,
            "password": "wrongpass"
        })
        assert response.status_code == 401
    
    def test_get_current_user(self, client):
        """测试获取当前用户信息"""
        username = self.get_unique_username()
        
        # 注册并登录
        client.post("/api/auth/register", json={
            "username": username,
            "email": f"{username}@example.com",
            "password": "testpass123"
        })
        login_res = client.post("/api/auth/login", json={
            "username": username,
            "password": "testpass123"
        })
        token = login_res.json()["data"]["access_token"]
        
        # 获取用户信息
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["username"] == username


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
