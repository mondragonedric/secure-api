from fastapi.testclient import TestClient

from main import app

client = TestClient(app)


def test_health_responde_ok():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_equipment_sin_token_da_401():
    r = client.get("/equipment")
    assert r.status_code == 401


def test_users_sin_token_da_401():
    r = client.get("/users")
    assert r.status_code == 401


def test_token_falso_da_401():
    r = client.get("/equipment", headers={"Authorization": "Bearer abc.def.ghi"})
    assert r.status_code == 401