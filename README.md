# API de Gestión de Tareas

API REST para gestionar el ciclo de vida de tareas (crear, consultar, actualizar y eliminar). Construida con **FastAPI** y **SQLAlchemy**, utiliza **SQLite** como base de datos y expone documentación interactiva autogenerada a través de Swagger UI.

El proyecto sirve como plantilla de referencia para servicios basados en FastAPI con persistencia en SQLite.

---

## Requisitos previos

| Requisito | Versión mínima |
|---|---|
| Python | 3.12+ |
| pip | incluido con Python |

### Dependencias del proyecto

| Paquete | Uso |
|---|---|
| FastAPI 0.136 | Framework web |
| SQLAlchemy 2.0 | ORM y acceso a datos |
| Pydantic 2 | Validación y serialización |
| Uvicorn | Servidor ASGI |
| pytest | Framework de tests |
| httpx | Cliente HTTP para tests |
| anyio | Soporte asíncrono para tests |

---

## Instalación

1. **Clonar el repositorio:**

   ```bash
   git clone https://github.com/DANACH666DJ/gestor-tareas-api.git
   cd gestor-tareas-api
   ```

2. **Crear y activar el entorno virtual:**

   ```bash
   python -m venv venv

   # macOS / Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. **Instalar dependencias:**

   ```bash
   pip install -r requirements.txt
   ```

---

## Arrancar la aplicación

```bash
uvicorn aplicacion.principal:app --reload
```

La API queda disponible en `http://127.0.0.1:8000`.

| Recurso | URL |
|---|---|
| API base | `http://127.0.0.1:8000` |
| Swagger UI | `http://127.0.0.1:8000/docs` |
| ReDoc | `http://127.0.0.1:8000/redoc` |

---

## Endpoints

Todos los endpoints operan bajo el prefijo `/tasks`.

Cada tarea tiene la siguiente estructura de respuesta:

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Actualizar el README del proyecto",
  "status": "pending",
  "priority": "medium",
  "created_at": "2025-05-27T14:00:00"
}
```

Los valores válidos para `status` son: `pending`, `in_progress` y `done`.

Los valores válidos para `priority` son: `low`, `medium` y `high` (por defecto `medium`).

---

### 1. Listar todas las tareas

| | |
|---|---|
| **Método** | `GET` |
| **Ruta** | `/tasks/` |
| **Parámetros de query** | `priority` (str, opcional) — Filtra por prioridad (`low`, `medium`, `high`) |

**Ejemplo curl:**

```bash
curl http://127.0.0.1:8000/tasks/
```

**Ejemplo de respuesta** (`200 OK`):

```json
[
  {
    "id": 1,
    "title": "Revisar documentación",
    "description": "Actualizar el README del proyecto",
    "status": "pending",
    "priority": "medium",
    "created_at": "2025-05-27T14:00:00"
  },
  {
    "id": 2,
    "title": "Corregir bug de login",
    "description": null,
    "status": "in_progress",
    "priority": "high",
    "created_at": "2025-05-27T15:30:00"
  }
]
```

---

### 2. Obtener una tarea por id

| | |
|---|---|
| **Método** | `GET` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |

**Ejemplo curl:**

```bash
curl http://127.0.0.1:8000/tasks/1
```

**Ejemplo de respuesta** (`200 OK`):

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Actualizar el README del proyecto",
  "status": "pending",
  "priority": "medium",
  "created_at": "2025-05-27T14:00:00"
}
```

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 3. Crear una nueva tarea

| | |
|---|---|
| **Método** | `POST` |
| **Ruta** | `/tasks/` |
| **Cuerpo (JSON)** | `title` (str, obligatorio, mínimo 3 caracteres), `description` (str, opcional), `status` (str, opcional, por defecto `"pending"`), `priority` (str, opcional, por defecto `"medium"`: `low`, `medium`, `high`) |

**Ejemplo curl:**

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Desplegar en producción", "description": "Subir la versión 2.0"}'
```

**Ejemplo de respuesta** (`201 Created`):

```json
{
  "id": 3,
  "title": "Desplegar en producción",
  "description": "Subir la versión 2.0",
  "status": "pending",
  "priority": "medium",
  "created_at": "2025-05-27T16:00:00"
}
```

**Respuesta de error** (`400 Bad Request`) — título con menos de 3 caracteres:

```json
{
  "detail": "El título debe tener al menos 3 caracteres"
}
```

---

### 4. Actualizar parcialmente una tarea

| | |
|---|---|
| **Método** | `PATCH` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |
| **Cuerpo (JSON)** | `title` (str, opcional), `description` (str, opcional), `status` (str, opcional), `priority` (str, opcional: `low`, `medium`, `high`) |

Solo se modifican los campos incluidos en el cuerpo de la petición. No se permite modificar una tarea cuyo estado sea `done`.

**Ejemplo curl:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "in_progress"}'
```

**Ejemplo de respuesta** (`200 OK`):

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Actualizar el README del proyecto",
  "status": "in_progress",
  "priority": "medium",
  "created_at": "2025-05-27T14:00:00"
}
```

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

**Respuesta de error** (`400 Bad Request`) — tarea ya completada:

```json
{
  "detail": "No se puede modificar una tarea ya completada"
}
```

---

### 5. Eliminar una tarea

| | |
|---|---|
| **Método** | `DELETE` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |

**Ejemplo curl:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

**Respuesta exitosa:** `204 No Content` (sin cuerpo).

**Respuesta de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

## Ejecutar los tests

```bash
pytest tests/ -v
```

Los tests utilizan una base de datos SQLite en memoria con `StaticPool`, lo que garantiza aislamiento total entre cada caso de prueba. No se accede al archivo `tareas.db` de producción durante la ejecución.

---

## Estructura del proyecto

```
gestor-tareas-api/
├── aplicacion/                 # Paquete principal de la aplicación
│   ├── __init__.py
│   ├── principal.py            # Punto de entrada: crea la instancia FastAPI y registra routers
│   ├── base_de_datos.py        # Configuración del engine, sesión de SQLAlchemy y dependencia get_db
│   ├── modelos.py              # Modelos ORM (tabla tasks) y enum TaskStatus
│   ├── esquemas.py             # Esquemas Pydantic de entrada (TaskCreate, TaskUpdate) y respuesta (TaskResponse)
│   └── rutas/                  # Paquete de endpoints agrupados por recurso
│       ├── __init__.py
│       └── tareas.py           # Endpoints REST para la gestión de tareas
├── tests/                      # Suite de tests automatizados
│   ├── __init__.py
│   └── test_tasks.py           # Tests de integración con pytest y SQLite en memoria
├── requirements.txt            # Dependencias de producción y desarrollo
├── AGENTS.md                   # Instrucciones y convenciones para Devin
├── README.md                   # Documentación del proyecto
└── .gitignore                  # Archivos y carpetas excluidos del control de versiones
```
