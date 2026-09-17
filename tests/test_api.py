from fastapi.testclient import TestClient

from aap.api import create_app


def test_demo_endpoint_returns_summary() -> None:
    client = TestClient(create_app())
    response = client.post("/api/demo/loop")
    assert response.status_code == 200
    data = response.json()
    assert data["summary"]["final_policy"] == "interrupt"
    assert data["summary"]["deterministic_violations"] == 1
