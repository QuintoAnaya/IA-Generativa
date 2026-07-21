"""
Evaluacion del Componente 1 sobre el dataset de casos clinicos.

Uso:
    python scripts/run_evaluacion.py                                          # 110 casos
    python scripts/run_evaluacion.py --manifest data_splits/train_cases.json  # solo train
    python scripts/run_evaluacion.py --manifest data_splits/test_cases.json   # solo test
    python scripts/run_evaluacion.py --guardar artifacts/resultados.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oncobridge.evaluation.evaluar import evaluate, print_report

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default=None,
                        help="Manifiesto de particion (train/test). Sin este argumento evalua los 110 casos.")
    parser.add_argument("--guardar", default=None, help="Ruta donde guardar el JSON de resultados")
    parser.add_argument("--silencioso", action="store_true", help="No imprimir caso por caso")
    args = parser.parse_args()

    results = evaluate(verbose=not args.silencioso, manifest=args.manifest)
    print_report(results)

    if args.guardar:
        Path(args.guardar).parent.mkdir(parents=True, exist_ok=True)
        Path(args.guardar).write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"\nResultados guardados en {args.guardar}")
