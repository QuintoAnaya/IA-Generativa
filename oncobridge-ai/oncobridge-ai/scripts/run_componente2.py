"""
Componente 2: genera la guia de lectura y la referencia visual prospectiva.

Uso:
    python scripts/run_componente1.py > artifacts/c1.json
    python scripts/run_componente2.py --c1 artifacts/c1.json
    python scripts/run_componente2.py --c1 artifacts/c1.json --device cuda
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oncobridge.pipeline import OncoBridgePipeline

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--c1", required=True, help="JSON de salida del Componente 1")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"],
                        help="Dispositivo para la generacion de imagen")
    parser.add_argument("--output-dir", default="output/generated_references")
    args = parser.parse_args()

    c1_output = json.loads(Path(args.c1).read_text(encoding="utf-8"))
    pipeline = OncoBridgePipeline(kb_path="data/knowledge_base")
    output = pipeline.run_component2(c1_output, device=args.device, output_dir=args.output_dir)
    print(json.dumps(output, indent=2, ensure_ascii=False))
