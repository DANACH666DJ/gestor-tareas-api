# Tests de la API de gestión de tareas con pytest y FastAPI TestClient

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# StaticPool garantiza que todas las sesiones comparten la misma conexión en memoria
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client():
    Base.metadata.create_all(bind=engine_test)
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine_test)


def _create_done_task(client):
    """Crea una tarea y la marca como 'done'; devuelve su id."""
    res = client.post("/tasks/", json={"title": "Tarea completada"})
    task_id = res.json()["id"]
    client.patch(f"/tasks/{task_id}", json={"status": "done"})
    return task_id


# ---------------------------------------------------------------------------
# PATCH /tasks/{id} — no se puede modificar una tarea con estado "done"
# ---------------------------------------------------------------------------

def test_actualizar_tarea_completada_devuelve_400(client):
    task_id = _create_done_task(client)

    response = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo título"})

    assert response.status_code == 400
    assert "completada" in response.json()["detail"].lower()


def test_actualizar_status_tarea_completada_devuelve_400(client):
    task_id = _create_done_task(client)

    response = client.patch(f"/tasks/{task_id}", json={"status": "pending"})

    assert response.status_code == 400


def test_actualizar_descripcion_tarea_completada_devuelve_400(client):
    task_id = _create_done_task(client)

    response = client.patch(
        f"/tasks/{task_id}", json={"description": "Nueva descripción"}
    )

    assert response.status_code == 400


def test_tarea_no_completada_se_puede_actualizar(client):
    res = client.post("/tasks/", json={"title": "Tarea pendiente"})
    task_id = res.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "Título actualizado"})

    assert response.status_code == 200
    assert response.json()["title"] == "Título actualizado"
