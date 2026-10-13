# Riesgo de deserción escolar en el Cauca 

> Pipeline que toma dos conjuntos de datos abiertos del MEN (instituciones educativas del Cauca y estadísticas educativas por municipio), los limpia, los cruza y calcula un nivel de riesgo de deserción por municipio, y los deja cargados en una base de datos SQL lista para análisis.

**Curso:** ETL — Maestría en Inteligencia Artificial y Ciencia de Datos, Universidad Autónoma de Occidente
**Periodo:** 2026-2
**Docente:** Fernando Barraza Alvarado

## Integrantes

| Nombre | Código | Usuario de GitHub |
|---|---|---|
| [Jenny Marcela Candelo] | [22615730] | [@gonzalessandra ] |

## Tabla de contenido

1. [Descripción del problema](#1-descripción-del-problema)
2. [Fuentes de datos](#2-fuentes-de-datos)
3. [Arquitectura del pipeline](#3-arquitectura-del-pipeline)
4. [Estructura del repositorio](#4-estructura-del-repositorio)
5. [Requisitos](#5-requisitos)
6. [Instalación y configuración](#6-instalación-y-configuración)
7. [Ejecución](#7-ejecución)
8. [Detalle de las etapas ETL](#8-detalle-de-las-etapas-etl)
9. [Modelo y diccionario de datos](#9-modelo-y-diccionario-de-datos)
10. [Calidad de datos y validaciones](#10-calidad-de-datos-y-validaciones)
11. [Resultados](#11-resultados)
12. [Limitaciones y trabajo futuro](#12-limitaciones-y-trabajo-futuro)
13. [Referencias](#13-referencias)

## 1. Descripción del problema

La deserción escolar es una de las principales barreras para la permanencia en el sistema educativo, y en un departamento con alta ruralidad como el Cauca su incidencia varía mucho entre municipios. La información necesaria para identificar dónde ocurre con más fuerza está repartida en conjuntos de datos distintos (estadísticas por municipio y listado de instituciones) que no están integrados ni listos para consulta.

**Objetivo:** dejar disponible, al final del pipeline, un conjunto de tablas integradas en una base de datos SQL que combine las tasas de deserción, cobertura, aprobación y repitencia de cada municipio del Cauca con las características de su oferta institucional (cantidad de colegios y proporción rural), junto con un nivel de riesgo (alto, medio, bajo). Sirve a secretarías de educación y analistas para priorizar municipios y como insumo para análisis o modelos de identificación temprana del riesgo.

## 2. Fuentes de datos

| Fuente | Tipo (CSV, API, BD, web) | Origen / URL | Tamaño aprox. | Frecuencia de actualización | Licencia |
|---|---|---|---|---|---|
| Instituciones Educativas de Cauca | CSV | Datos abiertos del MEN / datos.gov.co [[https://www.datos.gov.co/d/rvze-dant](https://www.datos.gov.co/Educaci-n/Instituciones-Educativas-de-Cauca/rvze-dant/about_data)] | 814 filas × 24 columnas (Cauca) | [Anual] | [licencia indicada en el portal] |
| MEN – Estadísticas en educación en preescolar, básica y media por municipio | CSV | Datos abiertos del MEN / datos.gov.co [https://www.datos.gov.co/Educaci-n/MEN_ESTADISTICAS_EN_EDUCACION_EN_PREESCOLAR-B-SICA/sras-4t5p/about_data] |15 707 filas × 41 columnas (todo el país); 42 municipios × 41 columnas (Cauca, 2024) | [Anual] | [licencia indicada en el portal] |

## 3. Arquitectura del pipeline

```mermaid
flowchart LR
    A[Instituciones Educativas de Cauca - CSV] --> E[Extract]
    B[MEN Estadísticas por municipio - CSV] --> E
    E --> R[(data/raw)]
    R --> T[Transform]
    T --> P[(data/processed)]
    P --> L[Load]
    L --> D[(SQLite / PostgreSQL)]
```

El flujo es por etapas desacopladas que se comunican a través de archivos: *extract* deja los CSV originales intactos en `data/raw/`, *transform* los lee, los limpia y escribe tablas en `data/processed/`, y *load* lee esas tablas y las carga en la base de datos. Así cada etapa se puede ejecutar y depurar por separado. Se eligió SQLite porque no requiere credenciales ni servidor. Las transformaciones reproducen y extienden la limpieza del notebook exploratorio (`notebooks/exploracion_entrega2.ipynb`).

**Tecnologías:** Python 3.11+, pandas, NumPy, python-dotenv, SQLite, SQLAlchemy y psycopg2, Mermaid.

## 4. Estructura del repositorio

```
├── data
│   ├── processed        <- Conjuntos de datos finales, listos para análisis o modelado.
│   └── raw              <- Datos originales, sin modificar.
├── docs                 <- Material de apoyo (capturas de evidencia).
├── extract              <- Código de extracción de datos.
├── transform            <- Código de limpieza y transformación.
├── load                 <- Código de carga al destino.
├── notebooks            <- Exploración inicial (entrega 2) que originó el pipeline.
├── tests                <- Pruebas de la etapa de transformación.
├── config.py            <- Rutas, nombres de archivo y parámetros del análisis.
├── pipeline.py          <- Orquesta la ejecución completa (extract → transform → load).
├── requirements.txt     <- Dependencias del proyecto.
├── .env.example         <- Variables de entorno (sin valores).
├── .gitignore           <- Archivos que git debe ignorar.
└── README.md            <- Este archivo.
```

## 5. Requisitos

- Python 3.11 o superior
- No se necesita ninguna base de datos instalada (SQLite viene con Python); 
- Dependencias listadas en `requirements.txt`

## 6. Instalación y configuración

```bash
# 1. Clonar el repositorio
git clone https://github.com/[gonzalessandra]/[Desercion-escolar].git
cd [Desercion-escolar]

# 2. Crear y activar el entorno virtual
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt
```

### Variables de entorno

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | Base de datos destino. Vacía = SQLite local | `postgresql://etl_user:***@localhost:5432/desercion` |
| `SQLITE_PATH` | Ruta del archivo SQLite (si no se usa `DATABASE_URL`) | `data/processed/desercion_cauca.db` |
| `INSTITUCIONES_URL` | URL de descarga del CSV de instituciones | https://www.datos.gov.co/Educaci-n/Instituciones-Educativas-de-Cauca/rvze-dant/about_data |
| `ESTADISTICAS_URL` | URL de descarga del CSV de estadísticas por municipio | https://www.datos.gov.co/Educaci-n/MEN_ESTADISTICAS_EN_EDUCACION_EN_PREESCOLAR-B-SICA/sras-4t5p/about_data |

### Obtención de los datos
Los datos provienen de datos abiertos del Ministerio de Educación Nacional de Colombia, publicados en datos.gov.co: el listado de Instituciones Educativas de Cauca y las Estadísticas en educación en preescolar, básica y media por municipio. Son archivos CSV de acceso público y agregados por municipio, sin datos personales de estudiantes.
Los dos CSV están incluidos en `data/raw/`

## 7. Ejecución

```bash
# Pipeline completo
python pipeline.py
```

```bash
# Por etapas (opcional)
python extract/extract.py
python transform/transform.py
python load/load.py
```

Para correr las pruebas: `pip install pytest && python -m pytest`.

**Salida esperada:** en `data/processed/` quedan `instituciones.csv`, `estadisticas_municipio.csv`, `municipios_riesgo.csv`, `reporte_calidad.csv` y `resumen_variables.csv`, y se crea la base `data/processed/desercion_cauca.db` con las cuatro primeras como tablas. La ejecución completa tarda menos de un segundo con estos datos.

Opcional: `python docs/generar_grafico.py` regenera la gráfica de resultados `docs/desercion_por_municipio.png`.

## 8. Detalle de las etapas ETL

### 8.1 Extract

- **Qué hace:** verifica que los dos CSV existan en `data/raw/` y valida que contengan las columnas necesarias. No modifica los datos originales.
- **Scripts:** `extract/extract.py`
- **Salida:** `data/raw/Instituciones_Educativas_de_Cauca.csv` y `data/raw/MEN_ESTADISTICAS_EN_EDUCACION_EN_PREESCOLAR__BASICA_Y_MEDIA_POR_MUNICIPIO.csv`

### 8.2 Transform

- **Qué hace:** filtra el Cauca y el año 2024 en las estadísticas, convierte a número las tasas que vienen como texto, unifica los valores de zona, cruza instituciones con municipios, resume la oferta institucional y calcula el nivel de riesgo de deserción.
- **Scripts:** `transform/transform.py`
- **Salida:** `data/processed/*.csv`

| # | Transformación | Justificación |
|---|---|---|
| 1 | Filtro de departamento Cauca y año 2024 | Los archivos fuente cubren más territorio y años que el alcance del proyecto. |
| 2 | Eliminación de duplicados por `codigoestablecimiento` y por `AÑO`, `CÓDIGO_MUNICIPIO` | Evita contar dos veces una institución o un municipio. |
| 3 | Conversión de texto a número en 33 columnas (`"13,06%"` → `0.1306`) | Las tasas llegan como texto con coma decimal y signo %; sin convertirlas no se pueden agregar ni comparar. Si la columna no trae %, solo se convierte la coma. |
| 4 | Unificación de `URBANA,RURAL` y `RURAL,URBANA` en `URBANA-RURAL` | Son la misma categoría escrita en distinto orden. |
| 5 | Nombres de columnas a minúsculas, sin tildes ni espacios | Evita problemas con caracteres especiales . |
| 6 | Código de municipio de cada institución, cruzando por nombre normalizado y usando el código del establecimiento solo como respaldo | El código del establecimiento no es confiable para ubicar el municipio: en 28 instituciones conserva el municipio de origen (p. ej. las de Sucre traen el código de Bolívar y las de Guachené el de Caloto). |
| 7 | Resumen por municipio: total de instituciones, rurales, urbanas, mixtas y % rural | Integra la oferta institucional con las estadísticas educativas. |
| 8 | Nivel de riesgo: `ALTO` si la deserción está en el percentil 75 o más, `MEDIO` si está en el percentil 50 o más, `BAJO` en otro caso | Clasificación relativa y simple para priorizar municipios; los umbrales se cambian en `config.py`. |

### 8.3 Load

- **Qué hace:** lee las tablas de `data/processed/` y las carga en la base de datos con reemplazo completo en cada ejecución; después verifica con `COUNT(*)` que las filas cargadas coinciden con las del archivo.
- **Scripts:** `load/load.py`
- **Destino:** base de datos SQLite (`data/processed/desercion_cauca.db`).

## 9. Modelo y diccionario de datos

```mermaid
erDiagram
    ESTADISTICAS_MUNICIPIO ||--|| MUNICIPIOS_RIESGO : "codigo_municipio"
    INSTITUCIONES }o--|| ESTADISTICAS_MUNICIPIO : "codigo_municipio"
    INSTITUCIONES {
        string codigoestablecimiento
        string nombreestablecimiento
        string zona
        int codigo_municipio
    }
    ESTADISTICAS_MUNICIPIO {
        int codigo_municipio
        string municipio
        float desercion
        float cobertura_neta
        float aprobacion
    }
    MUNICIPIOS_RIESGO {
        int codigo_municipio
        float desercion
        int total_instituciones
        float pct_instituciones_rurales
        string riesgo_desercion
        int ranking_desercion
    }
```

**Tabla / archivo:** `municipios_riesgo` (tabla principal para análisis; una fila por municipio)

| Columna | Tipo | Descripción | Ejemplo |
|---|---|---|---|
| `codigo_municipio` | int | Código DANE del municipio | 19701 |
| `municipio` | text | Nombre del municipio | Santa Rosa |
| `desercion` | float | Tasa de deserción intra-anual (proporción 0–1) | 0.0586 |
| `desercion_transicion`, `desercion_primaria`, `desercion_secundaria`, `desercion_media` | float | Deserción por nivel educativo | 0.0374 |
| `cobertura_neta`, `cobertura_bruta` (y por nivel) | float | Tasas de cobertura (proporción) | 0.7714 |
| `aprobacion`, `reprobacion`, `repitencia` (y por nivel) | float | Indicadores de eficiencia interna (proporción) | 0.8699 |
| `tamano_promedio_de_grupo` | float | Estudiantes promedio por grupo (viene vacía en el Cauca 2024) | — |
| `sedes_conectadas_a_internet` | float | Proporción de sedes con conexión a internet (viene vacía en el Cauca 2024) | — |
| `total_instituciones` | int | Instituciones educativas del municipio | 9 |
| `instituciones_rurales`, `instituciones_urbanas`, `instituciones_mixtas` | int | Instituciones por zona | 8 |
| `pct_instituciones_rurales` | float | Instituciones rurales / total | 0.89 |
| `riesgo_desercion` | text | `ALTO`, `MEDIO`, `BAJO` o `SIN_DATO` | ALTO |
| `ranking_desercion` | int | Posición del municipio por deserción (1 = mayor) | 1 |

Las demás columnas de estadísticas (`ano`, `poblacion_5_16`, etc.) conservan el significado del dataset original del MEN. Las tablas `instituciones` (una fila por establecimiento), `estadisticas_municipio` (estadísticas ya limpias) y `reporte_calidad` (verificaciones antes/después) completan el modelo.

## 10. Calidad de datos y validaciones

Cada ejecución genera `data/processed/reporte_calidad.csv` (también cargado como tabla `reporte_calidad`) y lo imprime en el log. Valores obtenidos en la última ejecución:

| Verificación | Antes | Después |
|---|---|---|
| Instituciones: número de registros | 814 | 814 |
| Instituciones: registros duplicados | 0 | 0 |
| Instituciones: nulos en columnas clave | 0 | 0 |
| Instituciones sin municipio asignado | — | 0 |
| Estadísticas: número de registros | 15 707 | 42 |
| Estadísticas: registros duplicados | 0 | 0 |
| Estadísticas: nulos en columnas clave | 142 | 0 |
| Deserción fuera del rango [0, 1] | — | 0 |
| Municipios sin instituciones tras el cruce | — | 0 |

"Antes" se mide sobre los archivos crudos completos (todo el país y todos los años en estadísticas) y "después" sobre los datos del Cauca en 2024. Las columnas `tamano_promedio_de_grupo` y `sedes_conectadas_a_internet` llegan 100 % vacías para el Cauca en 2024 en la fuente; se conservan en las tablas pero no se usan en el análisis.

Adicionalmente, `load/load.py` falla si el número de filas cargadas en la base no coincide con el del archivo procesado, y `tests/test_transform.py` prueba la limpieza y el cruce con datos sintéticos.

## 11. Resultados

El pipeline integra 814 instituciones y 42 municipios del Cauca. La tasa de deserción municipal va de 1,70 % a 5,86 % (promedio 3,18 %). Con los percentiles 50 y 75 como umbrales, 11 municipios quedan en riesgo ALTO, 10 en MEDIO y 21 en BAJO. Los más altos son Santa Rosa (5,86 %), Florencia (5,67 %) y Balboa (5,29 %). Los municipios de riesgo alto tienen en promedio una mayor proporción de instituciones rurales (84 %) que los de riesgo bajo (74 %), pero la correlación entre ambas variables es débil (0,10), así que la ruralidad por sí sola no explica la deserción; la aprobación sí tiene una relación inversa más marcada (−0,49).

```sql
-- Municipios con mayor deserción y su proporción de instituciones rurales
SELECT municipio, desercion, pct_instituciones_rurales, riesgo_desercion
FROM municipios_riesgo
ORDER BY ranking_desercion
LIMIT 10;
```

```sql
-- Cantidad de municipios por nivel de riesgo
SELECT riesgo_desercion, COUNT(*) AS municipios
FROM municipios_riesgo
GROUP BY riesgo_desercion;
```

![Deserción por municipio y nivel de riesgo](docs/desercion_por_municipio.png)

## 12. Limitaciones y trabajo futuro

- El análisis cubre un solo año (2024) y la granularidad es municipal: no identifica estudiantes ni instituciones en riesgo.
- El nivel de riesgo es una clasificación relativa por percentiles de la tasa de deserción, no un modelo predictivo validado; ALTO significa "entre los más altos del Cauca", no un umbral absoluto.
- El cruce entre fuentes depende de que el nombre del municipio coincida en ambos archivos (tras quitar tildes y mayúsculas); si el MEN cambia la escritura, el reporte de calidad lo evidenciará.
- Dos indicadores (tamaño promedio de grupo y sedes conectadas a internet) vienen vacíos para el Cauca en 2024, por lo que no pudieron incorporarse al análisis.
- Mejoras posibles: incluir varios años para ver tendencias, carga incremental, orquestación programada y un modelo de clasificación entrenado con la serie histórica.

## 13. Referencias

- Ministerio de Educación Nacional de Colombia, datos abiertos: https://www.mineducacion.gov.co/portal/estadisticas/datos-abiertos-men/
- Conjuntos de datos "Instituciones Educativas de Cauca": https://www.datos.gov.co/Educaci-n/Instituciones-Educativas-de-Cauca/rvze-dant/about_data
-  Conjuntos de datos "MEN Estadísticas en educación en preescolar, básica y media por municipio": https://www.datos.gov.co/Educaci-n/MEN_ESTADISTICAS_EN_EDUCACION_EN_PREESCOLAR-B-SICA/sras-4t5p/about_data
- Uso de IA generativa: se usó Claude para estructurar el repositorio a partir del notebook de la entrega 2 y el borrador de este README.
