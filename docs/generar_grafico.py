"""Genera docs/desercion_por_municipio.png a partir de la tabla municipios_riesgo (evidencia de resultados)."""
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

RAIZ = Path(__file__).resolve().parents[1]
df = pd.read_csv(RAIZ / "data" / "processed" / "municipios_riesgo.csv").sort_values("desercion")
colores = {"ALTO": "#c0392b", "MEDIO": "#e6a23c", "BAJO": "#4a90a4", "SIN_DATO": "#999999"}

fig, ax = plt.subplots(figsize=(9, 10))
ax.barh(df["municipio"], df["desercion"] * 100, color=df["riesgo_desercion"].map(colores))
ax.set_xlabel("Tasa de deserción (%)")
ax.set_title("Deserción escolar por municipio del Cauca (2024) y nivel de riesgo")
ax.legend(handles=[plt.Rectangle((0, 0), 1, 1, color=c) for c in list(colores.values())[:3]],
          labels=["Riesgo alto", "Riesgo medio", "Riesgo bajo"], loc="lower right")
fig.tight_layout()
fig.savefig(RAIZ / "docs" / "desercion_por_municipio.png", dpi=130)
