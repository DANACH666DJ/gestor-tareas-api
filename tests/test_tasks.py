# Tests de integración para los endpoints de tareas

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Base de datos SQLite en memoria para aislamiento entre tests
SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Fixture: cliente de prueba con la BD recreada en cada test
client = TestClient(app)


def setup_function():
    """Recrea las tablas antes de cada test para garantizar aislamiento."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# ---------- Tests para DELETE /tasks/ (eliminar todas) ----------


def test_delete_all_tasks_removes_every_task():
    """Verifica que DELETE /tasks/ elimina todas las tareas existentes."""
    # Crear varias tareas
    client.post("/tasks/", json={"title": "Tarea uno"})
    client.post("/tasks/", json={"title": "Tarea dos"})
    client.post("/tasks/", json={"title": "Tarea tres"})

    # Confirmar que existen tareas
    response = client.get("/tasks/")
    assert len(response.json()) == 3

    # Eliminar todas
    response = client.delete("/tasks/")
    assert response.status_code == 204

    # Verificar que la lista queda vacía
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []


def test_delete_all_tasks_on_empty_database():
    """Verifica que DELETE /tasks/ devuelve 204 incluso si no hay tareas."""
    response = client.delete("/tasks/")
    assert response.status_code == 204

    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json() == []
