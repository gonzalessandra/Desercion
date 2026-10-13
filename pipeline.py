"""Orquesta el pipeline completo: extract -> transform -> load.

Uso:
    python pipeline.py                   # pipeline completo
    python pipeline.py --stage transform # solo una etapa
"""
import argparse
import logging
import time

from extract.extract import extract
from load.load import load
from transform.transform import transform

log = logging.getLogger("pipeline")

ETAPAS = {"extract": extract, "transform": transform, "load": load}


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline ETL de deserción escolar en el Cauca")
    parser.add_argument("--stage", choices=[*ETAPAS, "all"], default="all")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

    seleccionadas = ETAPAS if args.stage == "all" else {args.stage: ETAPAS[args.stage]}
    inicio = time.time()
    for nombre, funcion in seleccionadas.items():
        log.info("=== Etapa: %s ===", nombre)
        funcion()
    log.info("Pipeline terminado en %.1f s", time.time() - inicio)


if __name__ == "__main__":
    main()
