"""Load: carga las tablas de data/processed/ en la base de datos destino.

Por defecto usa SQLite (archivo local, sin credenciales). Si se define DATABASE_URL en .env
(p. ej. PostgreSQL) se usa esa base mediante SQLAlchemy. Modo de carga: reemplazo completo.
"""
import logging
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

import config

log = logging.getLogger(__name__)


def _conectar():
    if config.DATABASE_URL:
        from sqlalchemy import create_engine  # solo se necesita para bases como PostgreSQL

        log.info("Destino: base de datos definida en DATABASE_URL")
        return create_engine(config.DATABASE_URL)
    config.SQLITE_PATH.parent.mkdir(parents=True, exist_ok=True)
    log.info("Destino: SQLite en %s", config.SQLITE_PATH)
    return sqlite3.connect(config.SQLITE_PATH)


def load(processed_dir: Path = config.PROCESSED_DIR) -> dict:
    """Carga cada tabla y devuelve {tabla: filas cargadas}, verificadas con COUNT(*)."""
    con = _conectar()
    conteos = {}
    try:
        for tabla in config.TABLAS:
            df = pd.read_csv(processed_dir / f"{tabla}.csv")
            df.to_sql(tabla, con, if_exists="replace", index=False)
            cargadas = int(pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {tabla}", con)["n"][0])
            if cargadas != len(df):
                raise RuntimeError(f"{tabla}: se esperaban {len(df)} filas y quedaron {cargadas}")
            conteos[tabla] = cargadas
            log.info("Tabla %-25s %5d filas cargadas", tabla, cargadas)
    finally:
        con.close() if hasattr(con, "close") else con.dispose()
    return conteos


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load()
