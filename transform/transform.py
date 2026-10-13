"""Transform: limpia, estandariza y une las dos fuentes; genera el nivel de riesgo por municipio.

Reproduce la limpieza del notebook exploratorio (notebooks/exploracion_entrega2.ipynb) y agrega
el cruce entre fuentes, el indicador de riesgo y el reporte de calidad.
"""
import logging
import re
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import numpy as np
import pandas as pd

import config

log = logging.getLogger(__name__)

# Columnas numéricas del dataset de estadísticas (algunas vienen como texto: "13,06%")
COLUMNAS_NUMERICAS = [
    "TASA_MATRICULACIÓN_5_16", "COBERTURA_NETA", "COBERTURA_NETA_TRANSICIÓN",
    "COBERTURA_NETA_PRIMARIA", "COBERTURA_NETA_SECUNDARIA", "COBERTURA_NETA_MEDIA",
    "COBERTURA_BRUTA", "COBERTURA_BRUTA_TRANSICIÓN", "COBERTURA_BRUTA_PRIMARIA",
    "COBERTURA_BRUTA_SECUNDARIA", "COBERTURA_BRUTA_MEDIA", "TAMAÑO_PROMEDIO_DE_GRUPO",
    "SEDES_CONECTADAS_A_INTERNET", "DESERCIÓN", "DESERCIÓN_TRANSICIÓN", "DESERCIÓN_PRIMARIA",
    "DESERCIÓN_SECUNDARIA", "DESERCIÓN_MEDIA", "APROBACIÓN", "APROBACIÓN_TRANSICIÓN",
    "APROBACIÓN_PRIMARIA", "APROBACIÓN_SECUNDARIA", "APROBACIÓN_MEDIA", "REPROBACIÓN",
    "REPROBACIÓN_TRANSICIÓN", "REPROBACIÓN_PRIMARIA", "REPROBACIÓN_SECUNDARIA",
    "REPROBACIÓN_MEDIA", "REPITENCIA", "REPITENCIA_TRANSICIÓN", "REPITENCIA_PRIMARIA",
    "REPITENCIA_SECUNDARIA", "REPITENCIA_MEDIA",
]

REEMPLAZOS_ZONA = {"URBANA,RURAL": "URBANA-RURAL", "RURAL,URBANA": "URBANA-RURAL"}

VARIABLES_RESUMEN = [
    "desercion", "aprobacion", "reprobacion", "repitencia", "cobertura_neta",
    "cobertura_bruta", "tasa_matriculacion_5_16", "sedes_conectadas_a_internet",
    "tamano_promedio_de_grupo",
]


# ---------------------------------------------------------------- utilidades
def _sin_tildes(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", texto) if not unicodedata.combining(c))


def normalizar_nombre(valor) -> str:
    """'Popayán ' -> 'POPAYAN' (para cruzar municipios por nombre)."""
    if pd.isna(valor):
        return ""
    return re.sub(r"\s+", " ", _sin_tildes(str(valor)).upper().strip())


def normalizar_columna(nombre: str) -> str:
    """'DESERCIÓN_MEDIA' -> 'desercion_media'; 'AÑO' -> 'ano'."""
    return re.sub(r"[^a-z0-9]+", "_", _sin_tildes(nombre).lower()).strip("_")


def a_numero(serie: pd.Series) -> pd.Series:
    """Convierte texto como '13,06%' o '23,5' en número.

    Si algún valor de la columna trae el signo %, la columna se expresa como proporción (0.1306).
    """
    texto = serie.astype("string").str.strip()
    es_porcentaje = texto.str.contains("%", regex=False).fillna(False).any()
    limpio = texto.str.replace("%", "", regex=False).str.replace(",", ".", regex=False)
    numero = pd.to_numeric(limpio, errors="coerce")
    return numero / 100 if es_porcentaje else numero


def leer_csv(ruta: Path) -> pd.DataFrame:
    try:
        return pd.read_csv(ruta)
    except UnicodeDecodeError:
        return pd.read_csv(ruta, encoding="latin-1")


# ---------------------------------------------------------------- calidad
def _metricas(df: pd.DataFrame, clave: list, columnas_clave: list) -> dict:
    return {
        "registros": int(len(df)),
        "duplicados": int(df.duplicated(subset=clave).sum()),
        "nulos_clave": int(df[columnas_clave].isna().sum().sum()),
    }


# ---------------------------------------------------------------- transformación (pura)
def transformar(inst_raw: pd.DataFrame, est_raw: pd.DataFrame, anio: int = config.ANIO_ANALISIS):
    """Devuelve (tablas, reporte_calidad, resumen_variables) a partir de los DataFrames crudos."""
    # --- Instituciones educativas
    antes_i = _metricas(inst_raw, ["codigoestablecimiento"],
                        ["codigoestablecimiento", "nombremunicipio", "zona"])
    inst = inst_raw[inst_raw["nombredepartamento"].str.strip().str.upper() == config.DEPARTAMENTO].copy()
    inst = inst.drop_duplicates(subset="codigoestablecimiento")
    inst["zona"] = inst["zona"].str.strip().str.upper().replace(REEMPLAZOS_ZONA)
    inst["municipio_key"] = inst["nombremunicipio"].map(normalizar_nombre)
    inst.columns = [normalizar_columna(c) for c in inst.columns]

    # --- Estadísticas por municipio
    antes_e = _metricas(est_raw, ["AÑO", "CÓDIGO_MUNICIPIO"], ["CÓDIGO_MUNICIPIO", "MUNICIPIO", "DESERCIÓN"])
    est = est_raw[
        (est_raw["DEPARTAMENTO"].str.strip().str.upper() == config.DEPARTAMENTO)
        & (pd.to_numeric(est_raw["AÑO"], errors="coerce") == anio)
    ].copy()
    est = est.drop_duplicates(subset=["AÑO", "CÓDIGO_MUNICIPIO"])
    for col in COLUMNAS_NUMERICAS:
        if col in est.columns:
            est[col] = a_numero(est[col])
    est["municipio_key"] = est["MUNICIPIO"].map(normalizar_nombre)
    est.columns = [normalizar_columna(c) for c in est.columns]
    est["codigo_municipio"] = est["codigo_municipio"].astype("Int64")

    # --- Código de municipio de cada institución: se cruza por nombre normalizado del municipio.
    #     El código del establecimiento (2xx.CCC.…) NO es confiable para esto: en algunos casos
    #     conserva el municipio de origen (p. ej. Sucre figura con el código de Bolívar), por lo
    #     que solo se usa como respaldo cuando el nombre no coincide.
    mapa = dict(zip(est["municipio_key"], est["codigo_municipio"]))
    inst["codigo_municipio"] = inst["municipio_key"].map(mapa).astype("Int64")
    digitos = inst["codigoestablecimiento"].astype("string").str.replace(r"\D", "", regex=True)
    respaldo = pd.to_numeric(digitos.str[1:6], errors="coerce").astype("Int64")
    sin_nombre = inst["codigo_municipio"].isna() & respaldo.isin(est["codigo_municipio"].dropna())
    inst.loc[sin_nombre, "codigo_municipio"] = respaldo[sin_nombre]
    inst["codigo_municipio"] = inst["codigo_municipio"].astype("Int64")

    # --- Resumen de instituciones por municipio y unión con las estadísticas
    resumen_inst = inst.groupby("codigo_municipio").agg(
        total_instituciones=("codigoestablecimiento", "count"),
        instituciones_rurales=("zona", lambda s: int((s == "RURAL").sum())),
        instituciones_urbanas=("zona", lambda s: int((s == "URBANA").sum())),
        instituciones_mixtas=("zona", lambda s: int((s == "URBANA-RURAL").sum())),
    ).reset_index()
    resumen_inst["pct_instituciones_rurales"] = (
        resumen_inst["instituciones_rurales"] / resumen_inst["total_instituciones"]
    )
    riesgo = est.merge(resumen_inst, on="codigo_municipio", how="left")
    conteos = ["total_instituciones", "instituciones_rurales", "instituciones_urbanas", "instituciones_mixtas"]
    sin_instituciones = int(riesgo["total_instituciones"].isna().sum())
    riesgo[conteos] = riesgo[conteos].fillna(0).astype(int)
    riesgo["pct_instituciones_rurales"] = riesgo["pct_instituciones_rurales"].fillna(0.0)

    # --- Nivel de riesgo de deserción (percentiles definidos en config.py)
    p_alto = riesgo["desercion"].quantile(config.PERCENTIL_RIESGO_ALTO)
    p_medio = riesgo["desercion"].quantile(config.PERCENTIL_RIESGO_MEDIO)
    riesgo["riesgo_desercion"] = np.select(
        [riesgo["desercion"].isna(), riesgo["desercion"] >= p_alto, riesgo["desercion"] >= p_medio],
        ["SIN_DATO", "ALTO", "MEDIO"],
        default="BAJO",
    )
    riesgo["ranking_desercion"] = riesgo["desercion"].rank(ascending=False, method="min").astype("Int64")
    riesgo = riesgo.sort_values("ranking_desercion").reset_index(drop=True)

    # --- Tablas finales (sin columnas auxiliares)
    est_final = est.drop(columns=["municipio_key"]).reset_index(drop=True)
    inst_final = inst.drop(columns=["municipio_key"]).reset_index(drop=True)
    riesgo_final = riesgo.drop(columns=["municipio_key"])

    # --- Reporte de calidad (antes / después)
    despues_i = _metricas(inst_final, ["codigoestablecimiento"],
                          ["codigoestablecimiento", "nombremunicipio", "zona"])
    despues_e = _metricas(est_final, ["ano", "codigo_municipio"], ["codigo_municipio", "municipio", "desercion"])
    fuera_rango = int(((est_final["desercion"] < 0) | (est_final["desercion"] > 1)).sum())
    inst_sin_municipio = int(inst_final["codigo_municipio"].isna().sum())
    filas = [
        ("Instituciones: número de registros", antes_i["registros"], despues_i["registros"]),
        ("Instituciones: registros duplicados", antes_i["duplicados"], despues_i["duplicados"]),
        ("Instituciones: nulos en columnas clave", antes_i["nulos_clave"], despues_i["nulos_clave"]),
        ("Instituciones sin municipio asignado", None, inst_sin_municipio),
        ("Estadísticas: número de registros", antes_e["registros"], despues_e["registros"]),
        ("Estadísticas: registros duplicados", antes_e["duplicados"], despues_e["duplicados"]),
        ("Estadísticas: nulos en columnas clave", antes_e["nulos_clave"], despues_e["nulos_clave"]),
        ("Deserción fuera del rango [0, 1]", None, fuera_rango),
        ("Municipios sin instituciones tras el cruce", None, sin_instituciones),
    ]
    calidad = pd.DataFrame(filas, columns=["verificacion", "antes", "despues"])
    calidad[["antes", "despues"]] = calidad[["antes", "despues"]].astype("Int64")

    presentes = [v for v in VARIABLES_RESUMEN if v in est_final.columns]
    resumen = (
        est_final[presentes].describe().T[["mean", "min", "max"]]
        .rename(columns={"mean": "media", "min": "minimo", "max": "maximo"})
        .rename_axis("variable").reset_index()
    )

    tablas = {
        "instituciones": inst_final,
        "estadisticas_municipio": est_final,
        "municipios_riesgo": riesgo_final,
        "reporte_calidad": calidad,
    }
    return tablas, calidad, resumen


# ---------------------------------------------------------------- etapa con lectura/escritura
def transform(raw_dir: Path = config.RAW_DIR, out_dir: Path = config.PROCESSED_DIR) -> dict:
    inst_raw = leer_csv(raw_dir / config.INSTITUCIONES_FILE)
    est_raw = leer_csv(raw_dir / config.ESTADISTICAS_FILE)
    log.info("Crudo: %d instituciones, %d filas de estadísticas", len(inst_raw), len(est_raw))

    tablas, calidad, resumen = transformar(inst_raw, est_raw)

    out_dir.mkdir(parents=True, exist_ok=True)
    for nombre, df in tablas.items():
        df.to_csv(out_dir / f"{nombre}.csv", index=False)
    resumen.to_csv(out_dir / "resumen_variables.csv", index=False)
    log.info("Reporte de calidad:\n%s", calidad.to_string(index=False))
    return tablas


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    transform()
