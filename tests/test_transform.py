"""Pruebas de la etapa Transform con datos sintéticos (ejecutar con: python -m pytest)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd

from transform.transform import a_numero, normalizar_columna, normalizar_nombre, transformar


def _datos_sinteticos():
    inst = pd.DataFrame({
        "nombredepartamento": ["CAUCA", "CAUCA", "CAUCA", "CAUCA", "NARIÑO"],
        "nombremunicipio": ["POPAYÁN", "POPAYÁN", "PUERTO TEJADA", "PUERTO TEJADA", "PASTO"],
        "codigoestablecimiento": ["319.001.003.379", "219.001.004.982", "219.573.000.082",
                                  "219.573.000.082", "252.001.000.001"],  # una fila duplicada
        "nombreestablecimiento": ["A", "B", "C", "C", "D"],
        "zona": ["URBANA", "RURAL", "RURAL,URBANA", "RURAL,URBANA", "URBANA"],
    })
    est = pd.DataFrame({
        "AÑO": [2024, 2024, 2023, 2024],
        "CÓDIGO_MUNICIPIO": [19001, 19573, 19001, 52001],
        "MUNICIPIO": ["Popayán", "Puerto Tejada", "Popayán", "Pasto"],
        "DEPARTAMENTO": ["Cauca", "Cauca", "Cauca", "Nariño"],
        "DESERCIÓN": ["3,68%", "9,50%", "4,00%", "1,00%"],
        "TAMAÑO_PROMEDIO_DE_GRUPO": ["24,5", "30,1", "25,0", "20,0"],
    })
    return inst, est


def test_cruce_prioriza_nombre_sobre_codigo_establecimiento():
    inst, est = _datos_sinteticos()
    # Institución de Puerto Tejada cuyo código de establecimiento trae el código de Popayán
    inst.loc[2, "codigoestablecimiento"] = "219.001.000.999"
    inst.loc[3, "codigoestablecimiento"] = "219.001.000.998"
    tablas, _, _ = transformar(inst, est, anio=2024)
    riesgo = tablas["municipios_riesgo"].set_index("codigo_municipio")
    assert riesgo.loc[19573, "total_instituciones"] == 2
    assert riesgo.loc[19001, "total_instituciones"] == 2


def test_a_numero_porcentaje_y_decimal():
    assert a_numero(pd.Series(["3,68%", "10%"])).tolist() == [0.0368, 0.10]
    assert a_numero(pd.Series(["24,5", "30"])).tolist() == [24.5, 30.0]


def test_normalizadores():
    assert normalizar_nombre(" Popayán ") == "POPAYAN"
    assert normalizar_columna("DESERCIÓN_MEDIA") == "desercion_media"
    assert normalizar_columna("AÑO") == "ano"


def test_transformar_filtra_limpia_y_cruza():
    inst, est = _datos_sinteticos()
    tablas, calidad, _ = transformar(inst, est, anio=2024)

    assert len(tablas["instituciones"]) == 3          # solo Cauca y sin duplicados
    assert set(tablas["instituciones"]["zona"]) == {"URBANA", "RURAL", "URBANA-RURAL"}
    assert len(tablas["estadisticas_municipio"]) == 2  # solo Cauca 2024

    riesgo = tablas["municipios_riesgo"].set_index("codigo_municipio")
    assert riesgo.loc[19001, "total_instituciones"] == 2
    assert riesgo.loc[19573, "instituciones_mixtas"] == 1
    assert riesgo.loc[19573, "riesgo_desercion"] == "ALTO"
    assert 0 <= riesgo["desercion"].max() <= 1
    assert abs(riesgo.loc[19001, "tamano_promedio_de_grupo"] - 24.5) < 1e-9

    despues = calidad.set_index("verificacion")["despues"]
    assert despues["Instituciones: registros duplicados"] == 0
    assert despues["Municipios sin instituciones tras el cruce"] == 0
