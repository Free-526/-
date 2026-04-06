"""
对话模块单元测试
"""
import pytest
import json


class TestChat:
    """对话接口测试"""
    
    def test_create_session(self, auth_client):
        """测试创建对话会话"""
        response = auth_client.post("/api/chat/sessions", json={
            "session_name": "测试会话"
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert "id" in data["data"]
        assert data["data"]["session_name"] == "测试会话"
    
    def test_get_sessions(self, auth_client):
        """测试获取会话列表"""
        # 先创建一个会话
        auth_client.post("/api/chat/sessions", json={"session_name": "测试会话2"})
        
        response = auth_client.get("/api/chat/sessions")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        # API返回结构: {"total": N, "items": [...]}
        assert "items" in data["data"]
        assert "total" in data["data"]
        assert isinstance(data["data"]["items"], list)
        assert data["data"]["total"] >= 1
    
    def test_send_message_session_not_found(self, auth_client):
        """测试向不存在的会话发送消息"""
        response = auth_client.post("/api/chat/send", json={
            "session_id": 99999,
            "message": "测试消息"
        })
        assert response.status_code == 404
    
    def test_delete_session_not_found(self, auth_client):
        """测试删除不存在的会话"""
        response = auth_client.delete("/api/chat/sessions/99999")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
