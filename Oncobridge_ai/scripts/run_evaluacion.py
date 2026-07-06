"""
CLI - Script de evaluacion. Corre el dataset completo y reporta metricas.

Uso:
    python scripts/run_evaluacion.py                     # imprime metricas
    python scripts/run_evaluacion.py --guardar out.json  # ademas guarda resultados
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse, json
from oncobridge.evaluation.evaluar import evaluar

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--guardar", default=None, help="ruta para guardar el JSON de resultados")
    args = ap.parse_args()

    resultados = evaluar(verbose=True)
    if args.guardar:
        with open(args.guardar, "w", encoding="utf-8") as f:
            json.dump(resultados, f, indent=2, ensure_ascii=False)
        print(f"\nResultados guardados en: {args.guardar}")

if __name__ == "__main__":
    main()
