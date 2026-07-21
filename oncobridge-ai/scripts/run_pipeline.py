"""
Flujo end-to-end: Componente 1 seguido de Componente 2.

Uso:
    python scripts/run_pipeline.py
    python scripts/run_pipeline.py --caso data/eval_dataset/clinical_cases/case_001/input.json
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oncobridge.pipeline import OncoBridgePipeline
from scripts.run_componente1 import EJEMPLO_POSITIVO

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--caso", default=None)
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--guardar", default=None)
    args = parser.parse_args()

    patient = json.loads(Path(args.caso).read_text(encoding="utf-8")) if args.caso else EJEMPLO_POSITIVO

    pipeline = OncoBridgePipeline(kb_path="data/knowledge_base")
    result = pipeline.run_end_to_end(patient, device=args.device)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    if args.guardar:
        Path(args.guardar).parent.mkdir(parents=True, exist_ok=True)
        Path(args.guardar).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
