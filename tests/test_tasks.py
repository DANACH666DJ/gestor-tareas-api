# Tests de integración para los endpoints de tareas

from fastapi.testclient import TestClient
from sqlalchemy import StaticPool, create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor SQLite en memoria para tests; StaticPool garantiza aislamiento
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

# Fixture: recrea las tablas antes de cada módulo de tests
Base.metadata.create_all(bind=engine_test)

client = TestClient(app)


# --- Helpers ---

def _create_task(**kwargs):
    """Crea una tarea con valores por defecto para simplificar los tests."""
    data = {"title": "Tarea de prueba", **kwargs}
    return client.post("/tasks/", json=data)


# --- Tests de creación ---

def test_create_task_with_categoria():
    """Verifica que se puede crear una tarea con categoría."""
    response = _create_task(categoria="Trabajo")
    assert response.status_code == 201
    body = response.json()
    assert body["categoria"] == "Trabajo"


def test_create_task_without_categoria():
    """Verifica que se puede crear una tarea sin categoría (campo nullable)."""
    response = _create_task()
    assert response.status_code == 201
    body = response.json()
    assert body["categoria"] is None


def test_create_task_categoria_too_short():
    """Verifica que una categoría con menos de 2 caracteres devuelve 400."""
    response = _create_task(categoria="A")
    assert response.status_code == 400
    assert response.json()["detail"] == "La categoría debe tener al menos 2 caracteres"


def test_create_task_categoria_empty_string():
    """Verifica que una categoría vacía devuelve 400."""
    response = _create_task(categoria="")
    assert response.status_code == 400
    assert response.json()["detail"] == "La categoría debe tener al menos 2 caracteres"


# --- Tests de actualización ---

def test_update_task_categoria():
    """Verifica que se puede actualizar la categoría de una tarea existente."""
    create_resp = _create_task(categoria="Personal")
    task_id = create_resp.json()["id"]

    update_resp = client.patch(f"/tasks/{task_id}", json={"categoria": "Trabajo"})
    assert update_resp.status_code == 200
    assert update_resp.json()["categoria"] == "Trabajo"


def test_update_task_set_categoria_to_null():
    """Verifica que se puede eliminar la categoría de una tarea."""
    create_resp = _create_task(categoria="Personal")
    task_id = create_resp.json()["id"]

    update_resp = client.patch(f"/tasks/{task_id}", json={"categoria": None})
    assert update_resp.status_code == 200
    assert update_resp.json()["categoria"] is None


# --- Tests de listado y obtención ---

def test_list_tasks_includes_categoria():
    """Verifica que la lista de tareas incluye el campo categoría."""
    _create_task(categoria="Urgente")
    response = client.get("/tasks/")
    assert response.status_code == 200
    tasks = response.json()
    assert any(t["categoria"] == "Urgente" for t in tasks)


def test_get_task_includes_categoria():
    """Verifica que la obtención de una tarea por id incluye el campo categoría."""
    create_resp = _create_task(categoria="Desarrollo")
    task_id = create_resp.json()["id"]

    response = client.get(f"/tasks/{task_id}")
    assert response.status_code == 200
    assert response.json()["categoria"] == "Desarrollo"
