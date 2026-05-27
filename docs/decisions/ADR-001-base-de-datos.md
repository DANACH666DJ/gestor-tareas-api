# ADR-001: Elección de SQLite como base de datos

## Estado

**Aceptado**

## Contexto

La API de Gestión de Tareas necesita una base de datos relacional para persistir tareas con sus atributos (título, descripción, estado y fecha de creación). El proyecto está diseñado como una API REST ligera construida con FastAPI y SQLAlchemy, orientada a entornos de desarrollo, prototipado rápido y despliegues de baja complejidad.

Los requisitos clave que condicionan la elección son:

- Simplicidad de despliegue: el equipo necesita arrancar la API sin infraestructura externa.
- Volumen de datos reducido: se espera un número moderado de tareas, sin concurrencia masiva.
- Portabilidad: la base de datos debe poder copiarse o recrearse fácilmente en cualquier entorno.
- Compatibilidad con SQLAlchemy 2.0: el ORM ya está integrado en el proyecto y debe funcionar sin adaptadores adicionales.

## Decisión

Se elige **SQLite** como motor de base de datos, almacenando los datos en un archivo local (`tareas.db`) en la raíz del proyecto.

### Razones principales

1. **Cero dependencias externas**: SQLite es una librería embebida incluida en la biblioteca estándar de Python (`sqlite3`). No requiere instalar ni administrar un servidor de base de datos.
2. **Configuración mínima**: basta con definir la URL de conexión `sqlite:///./tareas.db` y el parámetro `check_same_thread=False` para integrarse con FastAPI.
3. **Portabilidad total**: toda la base de datos reside en un único archivo que se puede copiar, versionar o eliminar fácilmente.
4. **Aislamiento en tests**: SQLAlchemy permite crear bases de datos SQLite en memoria con `StaticPool`, lo que garantiza tests rápidos y aislados sin tocar datos de producción.
5. **Adecuado para el alcance del proyecto**: el volumen de datos y la concurrencia esperados están dentro de los límites de rendimiento de SQLite.

## Alternativas consideradas

### PostgreSQL

**Ventajas:**
- Soporte completo de transacciones ACID con concurrencia real (MVCC).
- Tipos de datos avanzados (JSON, arrays, rangos, UUID nativo).
- Escalabilidad horizontal mediante réplicas de lectura.
- Ecosistema maduro con herramientas de monitorización, respaldo y extensiones (PostGIS, pg_trgm, etc.).
- Ideal para entornos de producción con múltiples usuarios concurrentes.

**Inconvenientes:**
- Requiere instalar y administrar un servidor independiente (o un contenedor Docker).
- Configuración más compleja: usuarios, roles, permisos, red.
- Mayor consumo de recursos (memoria y CPU) incluso en reposo.
- Añade dependencias adicionales al proyecto (`psycopg2` o `asyncpg`).
- Sobredimensionado para una API de tareas con volumen reducido.

### MySQL

**Ventajas:**
- Motor ampliamente adoptado con gran comunidad y documentación.
- Buen rendimiento en operaciones de lectura intensiva.
- Herramientas maduras de administración (MySQL Workbench, phpMyAdmin).
- Soporte de replicación maestro-esclavo.
- Compatible con la mayoría de proveedores de hosting.

**Inconvenientes:**
- Requiere un servidor independiente, similar a PostgreSQL.
- Implementación de transacciones menos robusta que PostgreSQL en algunos motores de almacenamiento.
- Menor riqueza de tipos de datos comparado con PostgreSQL.
- Dependencia adicional (`mysqlclient` o `PyMySQL`).
- Configuración y mantenimiento innecesarios para el alcance actual del proyecto.

## Consecuencias

### Positivas

- **Arranque inmediato**: cualquier desarrollador puede clonar el repositorio y ejecutar `uvicorn aplicacion.principal:app --reload` sin configurar infraestructura adicional.
- **Tests deterministas**: la estrategia de SQLite en memoria con `StaticPool` garantiza ejecución rápida y aislada del suite de tests.
- **Bajo coste operativo**: no hay servidor de base de datos que monitorizar, actualizar o respaldar de forma independiente.

### Negativas y riesgos a largo plazo

- **Concurrencia limitada**: SQLite usa un bloqueo a nivel de archivo para escrituras. Si la API escala a múltiples workers con escrituras simultáneas, se producirán bloqueos y errores `database is locked`.
- **Sin soporte multiusuario real**: no existe control de acceso a nivel de base de datos (usuarios, roles, permisos).
- **Migración futura**: si el proyecto crece, será necesario migrar a PostgreSQL u otro motor cliente-servidor. Aunque SQLAlchemy abstrae gran parte de la capa de datos, pueden surgir incompatibilidades en tipos de datos, funciones SQL específicas o comportamientos de bloqueo.
- **Sin réplicas ni alta disponibilidad**: SQLite no soporta replicación nativa. En un entorno de producción con requisitos de disponibilidad, esto es una limitación importante.
- **Respaldo en caliente complejo**: copiar el archivo `tareas.db` mientras la aplicación está escribiendo puede producir datos corruptos si no se usa la API de backup de SQLite.

### Plan de mitigación

- Mantener el acceso a datos detrás de la abstracción de SQLAlchemy para facilitar un cambio de motor en el futuro.
- Documentar la limitación de concurrencia en el README del proyecto.
- Si el proyecto evoluciona hacia producción con múltiples usuarios, evaluar la migración a PostgreSQL como siguiente ADR.
