from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200


def test_health_response():
    response = client.get("/health")
    data = response.json()

    assert data["status"] == "healthy"
    assert data["service"] == "CogniStream API"
    assert data["message"] == "API is running successfully"


def test_swagger_docs():
    response = client.get("/docs")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_openapi_schema():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert response.json()["info"]["title"] == "CogniStream API"


def test_invalid_endpoint():
    response = client.get("/invalid-endpoint")

    assert response.status_code == 404
