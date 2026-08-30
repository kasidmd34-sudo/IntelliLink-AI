from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_health():
    """Test that the FastAPI application is running."""
    response = client.get("/health")

    assert response.status_code == 200

    data = response.json()

    print("\n=== Health Response ===")
    print(data)


def test_openapi_docs():
    """Test that the API OpenAPI schema is available."""
    response = client.get("/openapi.json")

    assert response.status_code == 200