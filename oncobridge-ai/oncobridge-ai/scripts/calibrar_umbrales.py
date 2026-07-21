"""
Calibracion de los umbrales de decision sobre la particion de entrenamiento.

Recorre una grilla de combinaciones de los tres umbrales que determinan
`recommendation` y selecciona la que maximiza la funcion objetivo, sujeta a una
restriccion de sensibilidad minima.

La funcion objetivo pondera accuracy de derivacion, sensibilidad y especificidad
en partes iguales. La restriccion de sensibilidad existe por criterio clinico y
no estadistico: en oncologia, no derivar a un paciente que si tenia una lesion
es un error de consecuencias mayores que derivar a uno que no la tenia, de modo
que no se aceptan configuraciones que compren especificidad a costa de bajar la
sensibilidad por debajo del piso indicado.

Se ejecuta unicamente sobre train. La particion de prueba no se utiliza en
ningun punto de este proceso.

Uso:
    python scripts/calibrar_umbrales.py
    python scripts/calibrar_umbrales.py --min-sensibilidad 0.85
"""

import argparse
import hashlib
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oncobridge.components import scoring
from oncobridge.evaluation.evaluar import evaluate
from oncobridge.pipeline import OncoBridgePipeline

GRID_DERIVAR = [0.40, 0.45, 0.50, 0.55, 0.60]
GRID_SEGUIMIENTO = [0.15, 0.20, 0.25, 0.30]
GRID_BENIGNO = [0.45, 0.50, 0.55, 0.60, 0.65]


def dataset_fingerprint(kb_path: str) -> str:
    """Huella del contenido de la base de conocimiento.

    Permite detectar que unos umbrales guardados fueron calibrados con otra
    version del ground truth, y evitar reutilizarlos por error.
    """
    digest = hashlib.sha256()
    for path in sorted(Path(kb_path).glob("*.json")):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()[:16]


def objective(metrics: dict) -> float:
    return (metrics["accuracy_derivacion"] + metrics["sensibilidad"] + metrics["especificidad"]) / 3


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", default="data_splits/train_cases.json")
    parser.add_argument("--min-sensibilidad", type=float, default=0.85)
    parser.add_argument("--salida", default="artifacts/best_thresholds.json")
    args = parser.parse_args()

    pipeline = OncoBridgePipeline(kb_path="data/knowledge_base", thresholds_path=None)

    trials, best = [], None
    total = len(GRID_DERIVAR) * len(GRID_SEGUIMIENTO) * len(GRID_BENIGNO)
    print(f"Evaluando {total} combinaciones sobre {args.manifest}\n")

    for derivar in GRID_DERIVAR:
        for seguimiento in GRID_SEGUIMIENTO:
            if seguimiento >= derivar:
                continue
            for benigno in GRID_BENIGNO:
                scoring.THRESHOLD_DERIVAR = derivar
                scoring.THRESHOLD_SEGUIMIENTO = seguimiento
                scoring.THRESHOLD_BENIGN_NO_REFERRAL = benigno

                metrics = evaluate(verbose=False, manifest=args.manifest, pipeline=pipeline)
                score = objective(metrics)
                trial = {
                    "threshold_derivar": derivar,
                    "threshold_seguimiento": seguimiento,
                    "threshold_benign_no_referral": benigno,
                    "objetivo": round(score, 4),
                    "accuracy_derivacion": round(metrics["accuracy_derivacion"], 4),
                    "sensibilidad": round(metrics["sensibilidad"], 4),
                    "especificidad": round(metrics["especificidad"], 4),
                }
                trials.append(trial)
                if metrics["sensibilidad"] < args.min_sensibilidad:
                    continue
                if best is None or score > best["objetivo"]:
                    best = trial

    if best is None:
        print(f"Ninguna combinacion alcanzo la sensibilidad minima de {args.min_sensibilidad}.")
        sys.exit(1)

    Path(args.salida).parent.mkdir(parents=True, exist_ok=True)
    Path(args.salida).write_text(json.dumps({
        "dataset_fingerprint": dataset_fingerprint("data/knowledge_base"),
        "manifest": args.manifest,
        "min_sensibilidad": args.min_sensibilidad,
        "best_thresholds": {
            "threshold_derivar": best["threshold_derivar"],
            "threshold_seguimiento": best["threshold_seguimiento"],
            "threshold_benign_no_referral": best["threshold_benign_no_referral"],
        },
        "metricas_en_train": {
            "accuracy_derivacion": best["accuracy_derivacion"],
            "sensibilidad": best["sensibilidad"],
            "especificidad": best["especificidad"],
        },
    }, indent=2, ensure_ascii=False), encoding="utf-8")

    trials.sort(key=lambda t: t["objetivo"], reverse=True)
    Path("artifacts/optimization_trials.json").write_text(
        json.dumps(trials, indent=2, ensure_ascii=False), encoding="utf-8")

    print("Mejor configuracion sobre train:")
    for k, v in best.items():
        print(f"  {k}: {v}")
    print(f"\nGuardado en {args.salida}")


if __name__ == "__main__":
    main()
