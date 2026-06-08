# Tests de integración para los endpoints REST de tareas

from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor SQLite en memoria con StaticPool para aislamiento entre tests
engine_test = create_engine(
    "sqlite://",
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


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    """Recrea las tablas antes de cada test para garantizar aislamiento."""
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)


# ─── POST /tasks/ ────────────────────────────────────────────────────────────

def test_create_task_happy_path():
    response = client.post("/tasks/", json={"title": "Tarea de prueba"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tarea de prueba"
    assert data["status"] == "pending"
    assert data["description"] is None
    assert "id" in data
    assert "created_at" in data


def test_create_task_with_all_fields():
    response = client.post(
        "/tasks/",
        json={
            "title": "Tarea completa",
            "description": "Descripción detallada",
            "status": "in_progress",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Tarea completa"
    assert data["description"] == "Descripción detallada"
    assert data["status"] == "in_progress"


def test_create_task_title_too_short():
    response = client.post("/tasks/", json={"title": "ab"})
    assert response.status_code == 400
    assert response.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_create_task_title_only_spaces():
    response = client.post("/tasks/", json={"title": "  a "})
    assert response.status_code == 400
    assert response.json()["detail"] == "El título debe tener al menos 3 caracteres"


def test_create_task_missing_title():
    response = client.post("/tasks/", json={})
    assert response.status_code == 422


def test_create_task_invalid_status():
    response = client.post(
        "/tasks/", json={"title": "Tarea inválida", "status": "unknown"}
    )
    assert response.status_code == 422


# ─── GET /tasks/ ──────────────────────────────────────────────────────────────

def test_list_tasks_empty():
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_returns_created():
    client.post("/tasks/", json={"title": "Primera tarea"})
    client.post("/tasks/", json={"title": "Segunda tarea"})
    response = client.get("/tasks/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    titles = {t["title"] for t in data}
    assert titles == {"Primera tarea", "Segunda tarea"}


# ─── GET /tasks/{id} ─────────────────────────────────────────────────────────

def test_get_task_by_id():
    create_resp = client.post("/tasks/", json={"title": "Tarea específica"})
    task_id = create_resp.json()["id"]
    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Tarea específica"


def test_get_task_not_found():
    response = client.get("/tasks/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ─── PATCH /tasks/{id} ───────────────────────────────────────────────────────

def test_update_task_title():
    create_resp = client.post("/tasks/", json={"title": "Título original"})
    task_id = create_resp.json()["id"]
    response = client.patch(f"/tasks/{task_id}", json={"title": "Título nuevo"})
    assert response.status_code == 200
    assert response.json()["title"] == "Título nuevo"


def test_update_task_status_to_in_progress():
    create_resp = client.post("/tasks/", json={"title": "Tarea pendiente"})
    task_id = create_resp.json()["id"]
    response = client.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert response.status_code == 200
    assert response.json()["status"] == "in_progress"


def test_update_task_description():
    create_resp = client.post("/tasks/", json={"title": "Sin descripción"})
    task_id = create_resp.json()["id"]
    response = client.patch(
        f"/tasks/{task_id}", json={"description": "Ahora tiene descripción"}
    )
    assert response.status_code == 200
    assert response.json()["description"] == "Ahora tiene descripción"


def test_update_task_not_found():
    response = client.patch("/tasks/9999", json={"title": "Inexistente"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_update_done_task_blocked():
    create_resp = client.post("/tasks/", json={"title": "Tarea a completar"})
    task_id = create_resp.json()["id"]
    client.patch(f"/tasks/{task_id}", json={"status": "done"})
    response = client.patch(f"/tasks/{task_id}", json={"title": "Cambio prohibido"})
    assert response.status_code == 400
    assert response.json()["detail"] == "No se puede modificar una tarea ya completada"


# ─── PATCH /tasks/{id}/complete ────────────────────────────────────────────────

def test_complete_task_happy_path():
    """Marca una tarea pendiente como completada y verifica el estado 'done'."""
    create_resp = client.post("/tasks/", json={"title": "Tarea por completar"})
    task_id = create_resp.json()["id"]
    response = client.patch(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "done"
    assert data["id"] == task_id


def test_complete_task_from_in_progress():
    """Marca una tarea en progreso como completada."""
    create_resp = client.post(
        "/tasks/", json={"title": "Tarea en progreso", "status": "in_progress"}
    )
    task_id = create_resp.json()["id"]
    response = client.patch(f"/tasks/{task_id}/complete")
    assert response.status_code == 200
    assert response.json()["status"] == "done"


def test_complete_task_already_done():
    """Intentar completar una tarea ya completada devuelve 400."""
    create_resp = client.post("/tasks/", json={"title": "Tarea ya hecha"})
    task_id = create_resp.json()["id"]
    client.patch(f"/tasks/{task_id}/complete")
    response = client.patch(f"/tasks/{task_id}/complete")
    assert response.status_code == 400
    assert response.json()["detail"] == "La tarea ya está completada"


def test_complete_task_not_found():
    """Intentar completar una tarea inexistente devuelve 404."""
    response = client.patch("/tasks/9999/complete")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ─── DELETE /tasks/{id} ───────────────────────────────────────────────────────

def test_delete_task():
    create_resp = client.post("/tasks/", json={"title": "Tarea a eliminar"})
    task_id = create_resp.json()["id"]
    response = client.delete(f"/tasks/{task_id}")
    assert response.status_code == 204
    # Verificar que ya no existe
    get_resp = client.get(f"/tasks/{task_id}")
    assert get_resp.status_code == 404


def test_delete_task_not_found():
    response = client.delete("/tasks/9999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"
