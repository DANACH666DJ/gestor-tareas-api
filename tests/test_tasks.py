# Tests de la API de gestión de tareas con pytest y FastAPI TestClient

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# StaticPool garantiza que todas las sesiones comparten la misma conexión en memoria;
# sin él cada sesión abriría una conexión nueva y vería una base de datos vacía distinta
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


def override_get_db():
    # Sustituye la dependencia de BD real por la sesión de test
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


# ---------------------------------------------------------------------------
# Happy path: crear tarea
# ---------------------------------------------------------------------------

def test_crear_tarea_correctamente(client):
    payload = {"title": "Tarea de prueba", "description": "Descripción de ejemplo"}
    response = client.post("/tasks/", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tarea de prueba"
    assert data["description"] == "Descripción de ejemplo"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data


# ---------------------------------------------------------------------------
# Happy path: listar tareas
# ---------------------------------------------------------------------------

def test_listar_tareas_vacio(client):
    response = client.get("/tasks/")

    assert response.status_code == 200
    assert response.json() == []


def test_listar_tareas_con_datos(client):
    client.post("/tasks/", json={"title": "Primera tarea"})
    client.post("/tasks/", json={"title": "Segunda tarea"})

    response = client.get("/tasks/")

    assert response.status_code == 200
    assert len(response.json()) == 2


# ---------------------------------------------------------------------------
# Casos de error
# ---------------------------------------------------------------------------

def test_crear_tarea_titulo_vacio(client):
    response = client.post("/tasks/", json={"title": ""})

    assert response.status_code == 400
    assert response.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_crear_tarea_titulo_corto(client):
    response = client.post("/tasks/", json={"title": "ab"})

    assert response.status_code == 400
    assert response.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_crear_tarea_titulo_solo_espacios(client):
    response = client.post("/tasks/", json={"title": "   "})

    assert response.status_code == 400
    assert response.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_obtener_tarea_no_encontrada(client):
    response = client.get("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_actualizar_tarea_completada(client):
    create_resp = client.post("/tasks/", json={"title": "Tarea completada", "status": "done"})
    task_id = create_resp.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo título"})

    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede modificar una tarea ya completada"


def test_actualizar_tarea_no_encontrada(client):
    response = client.patch("/tasks/9999", json={"title": "No existe"})

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_eliminar_tarea_no_encontrada(client):
    response = client.delete("/tasks/9999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
