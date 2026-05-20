# Tests para el endpoint GET /tasks/status/{status}

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

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
client = TestClient(app)


def setup_function():
    Base.metadata.create_all(bind=engine)


def teardown_function():
    Base.metadata.drop_all(bind=engine)


def _create_task(title="Test task", description=None, status="pending"):
    payload = {"title": title, "status": status}
    if description:
        payload["description"] = description
    return client.post("/tasks/", json=payload)


def test_filter_by_pending():
    _create_task(title="Tarea pendiente", status="pending")
    _create_task(title="Tarea en progreso", status="in_progress")

    resp = client.get("/tasks/status/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "pending"


def test_filter_by_in_progress():
    _create_task(title="Tarea pendiente", status="pending")
    _create_task(title="Tarea en progreso", status="in_progress")

    resp = client.get("/tasks/status/in_progress")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "in_progress"


def test_filter_by_done():
    _create_task(title="Tarea pendiente", status="pending")
    _create_task(title="Tarea hecha", status="done")

    resp = client.get("/tasks/status/done")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["status"] == "done"


def test_filter_returns_empty_list():
    _create_task(title="Tarea pendiente", status="pending")

    resp = client.get("/tasks/status/done")
    assert resp.status_code == 200
    assert resp.json() == []


def test_filter_invalid_status_returns_422():
    resp = client.get("/tasks/status/invalid")
    assert resp.status_code == 422
