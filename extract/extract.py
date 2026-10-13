"""Extract: deja en data/raw/ los dos CSV originales (sin modificarlos) y valida su estructura."""
import logging
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

import config

log = logging.getLogger(__name__)

COLUMNAS_REQUERIDAS = {
    "instituciones": ["nombredepartamento", "nombremunicipio", "codigoestablecimiento", "zona"],
    "estadisticas": ["AÑO", "CÓDIGO_MUNICIPIO", "MUNICIPIO", "DEPARTAMENTO", "DESERCIÓN"],
}


def _descargar(url: str, destino: Path) -> None:
    log.info("Descargando %s -> %s", url, destino)
    urllib.request.urlretrieve(url, destino)


def _validar_columnas(clave: str, ruta: Path) -> None:
    columnas = pd.read_csv(ruta, nrows=0).columns
    faltantes = [c for c in COLUMNAS_REQUERIDAS[clave] if c not in columnas]
    if faltantes:
        raise ValueError(f"{ruta.name}: faltan las columnas {faltantes}")


def extract(raw_dir: Path = config.RAW_DIR) -> dict:
    """Garantiza que los archivos crudos existan en raw_dir y devuelve sus rutas."""
    raw_dir.mkdir(parents=True, exist_ok=True)
    fuentes = {
        "instituciones": (config.INSTITUCIONES_FILE, config.INSTITUCIONES_URL),
        "estadisticas": (config.ESTADISTICAS_FILE, config.ESTADISTICAS_URL),
    }
    rutas = {}
    for clave, (nombre, url) in fuentes.items():
        destino = raw_dir / nombre
        if not destino.exists():
            if not url:
                raise FileNotFoundError(
                    f"No se encontró {destino}. Copie el CSV en data/raw/ o defina "
                    f"la URL de descarga en el archivo .env (ver README, sección 6)."
                )
            _descargar(url, destino)
        _validar_columnas(clave, destino)
        log.info("Fuente '%s' lista: %s", clave, destino.name)
        rutas[clave] = destino
    return rutas


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    extract()
