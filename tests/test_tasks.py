# Tests para los endpoints de gestión de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor en memoria con StaticPool para aislamiento total entre tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    """Crea las tablas, inyecta la sesión de test y devuelve un TestClient."""
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


# ---------------------------------------------------------------------------
# Tests de validación de título en update_task (PATCH /tasks/{id})
# ---------------------------------------------------------------------------


def test_update_task_titulo_corto_devuelve_422(client):
    """Un título con menos de 3 caracteres en PATCH debe devolver 422."""
    resp = client.post("/tasks/", json={"title": "Tarea válida"})
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": "ab"})

    assert resp.status_code == 422
    assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_update_task_titulo_solo_espacios_devuelve_422(client):
    """Un título compuesto solo de espacios se considera vacío y devuelve 422."""
    resp = client.post("/tasks/", json={"title": "Tarea válida"})
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": "  "})

    assert resp.status_code == 422
    assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_update_task_titulo_vacio_devuelve_422(client):
    """Un título vacío devuelve 422."""
    resp = client.post("/tasks/", json={"title": "Tarea válida"})
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": ""})

    assert resp.status_code == 422
    assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_update_task_titulo_valido_actualiza_correctamente(client):
    """Un título con 3 o más caracteres se acepta y la tarea se actualiza."""
    resp = client.post("/tasks/", json={"title": "Tarea original"})
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo título"})

    assert resp.status_code == 200
    assert resp.json()["title"] == "Nuevo título"


def test_update_task_sin_titulo_no_dispara_validacion(client):
    """Si no se envía título, la validación no aplica y el PATCH procede."""
    resp = client.post("/tasks/", json={"title": "Tarea original"})
    task_id = resp.json()["id"]

    resp = client.patch(f"/tasks/{task_id}", json={"description": "Nueva desc"})

    assert resp.status_code == 200
    assert resp.json()["description"] == "Nueva desc"
