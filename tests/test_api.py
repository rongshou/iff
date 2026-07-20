"""API 集成测试。
"""
import os

# 必须在任何其他导入之前强制设定授权码，否则 Settings() 单例已被实例化
os.environ.setdefault("TIANQUAN_VALID_AUTH_CODES", "88888888")

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)
AUTH_HEADERS = {"X-Auth-Code": os.environ["TIANQUAN_VALID_AUTH_CODES"].split(",")[0]}


class TestHealth:
    def test_health_returns_ok(self):
        resp = client.get("/api/health")
        assert resp.status_code == 200
        assert resp.json().get("status") == "ok"


class TestSchoolAbbreviations:
    def test_returns_dict(self):
        resp = client.get("/api/school/abbreviations", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert "abbreviations" in data
        assert "total" in data

    def test_has_entries(self):
        resp = client.get("/api/school/abbreviations", headers=AUTH_HEADERS)
        assert resp.json()["total"] > 0


class TestVerifyAuthCode:
    def test_valid_code(self):
        resp = client.post("/api/verify-auth-code", json={"auth_code": "88888888"})
        assert resp.status_code == 200
        assert resp.json().get("valid") is True

    def test_invalid_code(self):
        resp = client.post("/api/verify-auth-code", json={"auth_code": "DEFINITELY-WRONG"})
        assert resp.status_code == 200
        assert resp.json().get("valid") is False


class TestTimelinePlan:
    def test_plan_with_params(self):
        resp = client.get("/api/timeline/plan", headers=AUTH_HEADERS, params={
            "school": "test_univ", "country": "US", "major": "CS",
        })
        assert resp.status_code == 200
        assert isinstance(resp.json(), dict)


class TestNews:
    @pytest.mark.skip(reason="werss.db not available in test env")
    def test_categories(self):
        resp = client.get("/api/news/categories")
        assert resp.status_code == 200

    @pytest.mark.skip(reason="werss.db not available in test env")
    def test_latest(self):
        resp = client.get("/api/news/latest")
        assert resp.status_code == 200


class TestMbti:
    def test_types_returns_dict(self):
        resp = client.get("/api/mbti/types", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert "types" in data
        assert len(data["types"]) > 0

    def test_majors_with_type(self):
        resp = client.get("/api/mbti/majors?mbti=INTJ", headers=AUTH_HEADERS)
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, dict)
        assert data.get("type") == "INTJ"
