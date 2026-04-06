"""
埋点模块单元测试
"""
import pytest
from datetime import datetime, timedelta

from app.core.analytics import Tracker


class TestAnalytics:
    """埋点功能测试"""
    
    def test_track_event_api(self, auth_client):
        """测试通过API上报事件"""
        response = auth_client.post("/api/analytics/track/event", json={
            "event_name": "test_event",
            "event_type": "click",
            "page_path": "/test",
            "properties": {"key": "value"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    def test_track_performance_api(self, auth_client):
        """测试通过API上报性能数据"""
        response = auth_client.post("/api/analytics/track/performance", json={
            "operation": "test_operation",
            "duration_ms": 100,
            "status": "success",
            "metadata": {"detail": "test"}
        })
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
    
    def test_get_dashboard(self, auth_client):
        """测试获取数据看板 - 需要管理员权限"""
        response = auth_client.get("/api/analytics/dashboard")
        # 普通用户无权限访问看板，应该返回403
        assert response.status_code == 200
        data = response.json()
        # API返回结构: {"code": 403, "message": "无权访问"}
        assert data["code"] == 403


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
