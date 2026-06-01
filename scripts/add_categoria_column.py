"""
Script de migración: añade la columna 'categoria' a la tabla 'tasks'.

Uso:
    source venv/bin/activate
    python scripts/add_categoria_column.py

La columna se crea como VARCHAR(100) NULL para mantener compatibilidad con
las tareas existentes que no tengan categoría asignada.

Si la columna ya existe, el script lo detecta y termina sin errores.
"""

import sqlite3
import sys

DB_PATH = "tareas.db"


def migrate():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Comprueba si la columna ya existe
    cursor.execute("PRAGMA table_info(tasks)")
    columns = [row[1] for row in cursor.fetchall()]

    if "categoria" in columns:
        print("La columna 'categoria' ya existe. No se requiere migración.")
        conn.close()
        return

    cursor.execute("ALTER TABLE tasks ADD COLUMN categoria VARCHAR(100) NULL")
    conn.commit()
    conn.close()
    print("Migración completada: columna 'categoria' añadida a la tabla 'tasks'.")


if __name__ == "__main__":
    try:
        migrate()
    except Exception as e:
        print(f"Error durante la migración: {e}", file=sys.stderr)
        sys.exit(1)
