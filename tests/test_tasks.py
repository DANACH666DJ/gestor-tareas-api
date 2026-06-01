# Tests de integración para los endpoints de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor SQLite en memoria con StaticPool para aislamiento entre tests
engine_test = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture()
def client():
    """Crea las tablas, inyecta la sesión de prueba y las elimina al terminar."""
    Base.metadata.create_all(bind=engine_test)

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
    Base.metadata.drop_all(bind=engine_test)


# ---------------------------------------------------------------------------
# Tests del campo prioridad
# ---------------------------------------------------------------------------


class TestCreateTaskPriority:
    """Verificar que el campo prioridad funciona correctamente al crear tareas."""

    def test_create_task_default_priority(self, client):
        """Al crear una tarea sin especificar prioridad, debe ser 'medium'."""
        response = client.post("/tasks/", json={"title": "Tarea sin prioridad"})
        assert response.status_code == 201
        data = response.json()
        assert data["priority"] == "medium"

    def test_create_task_with_low_priority(self, client):
        """Al crear una tarea con prioridad 'low', se almacena correctamente."""
        response = client.post(
            "/tasks/", json={"title": "Tarea baja", "priority": "low"}
        )
        assert response.status_code == 201
        assert response.json()["priority"] == "low"

    def test_create_task_with_high_priority(self, client):
        """Al crear una tarea con prioridad 'high', se almacena correctamente."""
        response = client.post(
            "/tasks/", json={"title": "Tarea urgente", "priority": "high"}
        )
        assert response.status_code == 201
        assert response.json()["priority"] == "high"

    def test_create_task_with_invalid_priority(self, client):
        """Al enviar un valor de prioridad no válido, la API rechaza la petición."""
        response = client.post(
            "/tasks/", json={"title": "Tarea inválida", "priority": "critical"}
        )
        assert response.status_code == 422


class TestUpdateTaskPriority:
    """Verificar que la prioridad se puede actualizar mediante PATCH."""

    def test_update_priority(self, client):
        """Actualizar la prioridad de una tarea existente."""
        create = client.post("/tasks/", json={"title": "Tarea para editar"})
        task_id = create.json()["id"]
        assert create.json()["priority"] == "medium"

        response = client.patch(f"/tasks/{task_id}", json={"priority": "high"})
        assert response.status_code == 200
        assert response.json()["priority"] == "high"

    def test_update_priority_invalid_value(self, client):
        """Actualizar con un valor de prioridad no válido devuelve 422."""
        create = client.post("/tasks/", json={"title": "Tarea para editar"})
        task_id = create.json()["id"]

        response = client.patch(
            f"/tasks/{task_id}", json={"priority": "urgent"}
        )
        assert response.status_code == 422

    def test_update_priority_on_done_task(self, client):
        """No se puede cambiar la prioridad de una tarea ya completada."""
        create = client.post("/tasks/", json={"title": "Tarea completada"})
        task_id = create.json()["id"]
        client.patch(f"/tasks/{task_id}", json={"status": "done"})

        response = client.patch(f"/tasks/{task_id}", json={"priority": "low"})
        assert response.status_code == 400
        assert response.json()["detail"] == "No se puede modificar una tarea ya completada"


class TestGetTaskPriority:
    """Verificar que la prioridad se devuelve en las respuestas GET."""

    def test_get_task_includes_priority(self, client):
        """El campo prioridad aparece en la respuesta de GET /tasks/{id}."""
        create = client.post(
            "/tasks/", json={"title": "Tarea con prioridad", "priority": "high"}
        )
        task_id = create.json()["id"]

        response = client.get(f"/tasks/{task_id}")
        assert response.status_code == 200
        assert response.json()["priority"] == "high"

    def test_list_tasks_includes_priority(self, client):
        """El campo prioridad aparece en cada elemento del listado."""
        client.post("/tasks/", json={"title": "Tarea uno", "priority": "low"})
        client.post("/tasks/", json={"title": "Tarea dos", "priority": "high"})

        response = client.get("/tasks/")
        assert response.status_code == 200
        priorities = [t["priority"] for t in response.json()]
        assert "low" in priorities
        assert "high" in priorities


class TestFilterByPriority:
    """Verificar el filtrado por prioridad en el listado de tareas."""

    def test_filter_by_priority(self, client):
        """Filtrar tareas por prioridad devuelve solo las que coinciden."""
        client.post("/tasks/", json={"title": "Baja uno", "priority": "low"})
        client.post("/tasks/", json={"title": "Alta uno", "priority": "high"})
        client.post("/tasks/", json={"title": "Baja dos", "priority": "low"})

        response = client.get("/tasks/", params={"priority": "low"})
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(t["priority"] == "low" for t in data)

    def test_filter_by_invalid_priority(self, client):
        """Filtrar con un valor de prioridad no válido devuelve 422."""
        response = client.get("/tasks/", params={"priority": "critical"})
        assert response.status_code == 422
