"""应用入口测试 —— 健康检查接口返回码与响应体校验。
"""

from fastapi.testclient import TestClient


def test_check_health(test_client: TestClient) -> None:
    response = test_client.get("/monitor/health/check/")
    assert response.status_code == 200
    body = response.json()
    assert body["success"] is True
    assert body["code"] == 0
