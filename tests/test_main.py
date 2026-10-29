from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root():
    r = client.get("/")
    assert r.status_code == 200
    assert r.json()["service"] == "deployment-tracker-api"


def test_health():
    assert client.get("/health").json() == {"status": "healthy"}


def test_create_and_get():
    r = client.post(
        "/api/deployments",
        json={"service": "api", "version": "v1.2.0", "environment": "staging", "status": "success"},
    )
    assert r.status_code == 201
    item = r.json()
    assert item["service"] == "api"
    got = client.get(f"/api/deployments/{item['id']}")
    assert got.status_code == 200
    assert got.json()["version"] == "v1.2.0"


def test_list_and_filter():
    client.post("/api/deployments", json={"service": "web", "version": "v2.0.0", "environment": "prod"})
    r = client.get("/api/deployments?environment=prod")
    assert r.status_code == 200
    assert all(d["environment"] == "prod" for d in r.json())
    assert len(r.json()) >= 1


def test_404():
    assert client.get("/api/deployments/nope").status_code == 404
    assert client.delete("/api/deployments/nope").status_code == 404


def test_delete():
    item = client.post("/api/deployments", json={"service": "x", "version": "v0.1.0"}).json()
    assert client.delete(f"/api/deployments/{item['id']}").status_code == 204
    assert client.get(f"/api/deployments/{item['id']}").status_code == 404


def test_validation_422():
    r = client.post("/api/deployments", json={"service": "", "version": "v1.0.0"})
    assert r.status_code == 422
    r = client.post(
        "/api/deployments",
        json={"service": "api", "version": "v1.0.0", "environment": "qa"},
    )
    assert r.status_code == 422


def test_metrics():
    client.post("/api/deployments", json={"service": "m", "version": "v1.0.0"})
    r = client.get("/metrics")
    assert r.status_code == 200
    assert "deployments_created_total" in r.text
    assert "deployments_total" in r.text
