"""
文献管理模块单元测试
"""
import pytest
import io


class TestPapers:
    """文献管理接口测试"""
    
    def test_get_papers_empty(self, auth_client):
        """测试获取空文献列表"""
        response = auth_client.get("/api/papers")
        assert response.status_code == 200
        data = response.json()
        assert data["code"] == 200
        assert data["data"]["items"] == []
    
    def test_upload_pdf_unauthorized(self, client):
        """测试未授权上传"""
        pdf_content = b"%PDF-1.4 fake pdf content"
        files = {
            "file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")
        }
        response = client.post("/api/papers/upload", files=files)
        # 可能是401或403，都视为未授权
        assert response.status_code in [401, 403]
    
    def test_delete_paper_not_found(self, auth_client):
        """测试删除不存在的文献"""
        response = auth_client.delete("/api/papers/99999")
        assert response.status_code == 404


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
