from fastapi.testclient import TestClient

from main import app

client = TestClient(app)

EQUIPO = {
    "name": "Laptop Test",
    "type": "laptop",
    "serial_number": "T-001",
    "status": "disponible",
}


def login(usuario, clave):
    return client.post("/login", data={"username": usuario, "password": clave})


def cabecera(usuario, clave):
    token = login(usuario, clave).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_login_correcto_da_token():
    r = login("admin_test", "ClaveAdmin123")
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_clave_incorrecta_da_401():
    assert login("admin_test", "mala").status_code == 401


def test_usuario_inexistente_y_clave_mala_dan_la_misma_respuesta():
    r1 = login("fantasma", "lo_que_sea")
    r2 = login("admin_test", "mala")
    assert r1.status_code == r2.status_code == 401
    assert r1.json() == r2.json()


def test_tecnico_puede_crear_equipo():
    h = cabecera("tecnico_test", "ClaveTecnico123")
    assert client.post("/equipment", json=EQUIPO, headers=h).status_code == 200


def test_tecnico_no_puede_borrar():
    h_admin = cabecera("admin_test", "ClaveAdmin123")
    creado = client.post("/equipment", json=EQUIPO, headers=h_admin).json()
    h_tec = cabecera("tecnico_test", "ClaveTecnico123")
    r = client.delete(f"/equipment/{creado['id']}", headers=h_tec)
    assert r.status_code == 403


def test_admin_puede_borrar():
    h = cabecera("admin_test", "ClaveAdmin123")
    creado = client.post("/equipment", json=EQUIPO, headers=h).json()
    assert client.delete(f"/equipment/{creado['id']}", headers=h).status_code == 200


def test_tecnico_no_puede_ver_usuarios():
    h = cabecera("tecnico_test", "ClaveTecnico123")
    assert client.get("/users", headers=h).status_code == 403


def test_serial_duplicado_da_409():
    h = cabecera("admin_test", "ClaveAdmin123")
    client.post("/equipment", json=EQUIPO, headers=h)
    assert client.post("/equipment", json=EQUIPO, headers=h).status_code == 409


def test_cinco_fallos_bloquean_el_login():
    for _ in range(5):
        assert login("admin_test", "mala").status_code == 401
    assert login("admin_test", "ClaveAdmin123").status_code == 429