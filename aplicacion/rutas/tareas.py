# Definición de los endpoints REST para la gestión de tareas

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task, TaskStatus

# Router con prefijo /tasks; agrupa todos los endpoints de tareas
router = APIRouter(prefix="/tasks", tags=["tasks"])


# Devuelve la lista completa de tareas almacenadas
@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """Devuelve la lista completa de tareas almacenadas.

    Args:
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        list[Task]: Todas las tareas registradas en la base de datos.
    """
    return db.query(Task).all()


# Devuelve una tarea por su identificador; 404 si no existe
@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Obtiene una tarea por su identificador.

    Args:
        task_id (int): Identificador único de la tarea.
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        Task: La tarea correspondiente al identificador proporcionado.

    Raises:
        HTTPException: 404 si no existe una tarea con el id indicado.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


# Crea una nueva tarea y devuelve el recurso creado con código 201
@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una nueva tarea y la persiste en la base de datos.

    Args:
        payload (TaskCreate): Esquema con los datos de la tarea a crear.
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        Task: La tarea recién creada con su id y fecha de creación asignados.

    Raises:
        HTTPException: 400 si el título tiene menos de 3 caracteres.
    """
    # Valida que el título tenga al menos 3 caracteres antes de persistir
    if len(payload.title.strip()) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El título debe tener al menos 3 caracteres",
        )
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


# Actualiza parcialmente una tarea; solo modifica los campos enviados en el cuerpo
@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Actualiza parcialmente una tarea existente.

    Solo modifica los campos incluidos en el cuerpo de la petición.

    Args:
        task_id (int): Identificador único de la tarea a actualizar.
        payload (TaskUpdate): Esquema con los campos a modificar.
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Returns:
        Task: La tarea actualizada con los nuevos valores.

    Raises:
        HTTPException: 404 si no existe una tarea con el id indicado.
        HTTPException: 400 si la tarea ya está en estado ``done``.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")

    # Una tarea ya completada no puede modificarse posteriormente
    if task.status == TaskStatus.done:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No se puede modificar una tarea ya completada",
        )

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


# Elimina una tarea de la base de datos; devuelve 204 sin cuerpo
@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea de la base de datos de forma permanente.

    Args:
        task_id (int): Identificador único de la tarea a eliminar.
        db (Session): Sesión de base de datos inyectada por FastAPI.

    Raises:
        HTTPException: 404 si no existe una tarea con el id indicado.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
