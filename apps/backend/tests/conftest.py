"""Configuración común de los tests.

Antes de importar la app se fijan las variables de entorno, porque la configuración
(src/shared/config.py) y la conexión a la base se crean una sola vez al importar:

- DATABASE_URL apunta a una base aparte, `postgrado_test` (en el mismo Postgres), así
  los tests nunca tocan los datos de desarrollo. Se puede cambiar con TEST_DATABASE_URL.
- Los emails quedan simulados y la tarea diaria de vencimientos, apagada.
- Los PDFs se guardan en una carpeta temporal.
"""
import os
import tempfile
from urllib.parse import urlsplit, urlunsplit

URL_POR_DEFECTO = "postgresql+asyncpg://postgrado_user:postgrado_dev_password@localhost:5432/postgrado_dev"


def _url_de_la_base_de_test() -> str:
    if os.environ.get("TEST_DATABASE_URL"):
        return os.environ["TEST_DATABASE_URL"]
    base = urlsplit(os.environ.get("DATABASE_URL", URL_POR_DEFECTO))
    return urlunsplit(base._replace(path="/postgrado_test"))


os.environ.update({
    "DATABASE_URL": _url_de_la_base_de_test(),
    "JWT_SECRET": "secreto-solo-para-los-tests-0123456789-abcdefghij",
    "EMAIL_MODO": "simulado",
    "TAREAS_PROGRAMADAS": "false",
    "STORAGE_PATH": tempfile.mkdtemp(prefix="posgrado-tests-"),
})