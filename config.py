"""Configuración central del pipeline ETL (rutas, nombres de archivo y parámetros)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent
RAW_DIR = ROOT / "data" / "raw"
PROCESSED_DIR = ROOT / "data" / "processed"

# Archivos de entrada (se esperan en data/raw/)
INSTITUCIONES_FILE = "Instituciones_Educativas_de_Cauca.csv"
ESTADISTICAS_FILE = "MEN_ESTADISTICAS_EN_EDUCACION_EN_PREESCOLAR__BASICA_Y_MEDIA_POR_MUNICIPIO.csv"

# URLs opcionales de descarga (si el archivo no está en data/raw/)
INSTITUCIONES_URL = os.getenv("INSTITUCIONES_URL")
ESTADISTICAS_URL = os.getenv("ESTADISTICAS_URL")

# Parámetros del análisis
DEPARTAMENTO = "CAUCA"
ANIO_ANALISIS = 2024

# Umbrales del nivel de riesgo por municipio (percentiles de la tasa de deserción)
PERCENTIL_RIESGO_ALTO = 0.75
PERCENTIL_RIESGO_MEDIO = 0.50

# Destino de la carga
DATABASE_URL = os.getenv("DATABASE_URL")  # opcional, p. ej. PostgreSQL
SQLITE_PATH = Path(os.getenv("SQLITE_PATH", PROCESSED_DIR / "desercion_cauca.db"))

# Tablas que se generan en transform/ y se cargan en load/ (nombre = nombre del CSV)
TABLAS = ["instituciones", "estadisticas_municipio", "municipios_riesgo", "reporte_calidad"]
