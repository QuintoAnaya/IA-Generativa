"""
Componente 2: genera el informe radiologico orientado y la referencia visual.

Uso:
    python scripts/run_componente1.py > artifacts/c1.json
    python scripts/run_componente2.py --c1 artifacts/c1.json
    python scripts/run_componente2.py --c1 artifacts/c1.json --imagen studies/estudio.png
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
    parser.add_argument("--imagen", default=None,
                        help="Ruta a un estudio de imagen del paciente (opcional). "
                             "El dataset no incluye imagenes; sin este argumento el "
                             "informe se arma sobre el patron esperado de la hipotesis.")
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"],
                        help="Dispositivo para la generacion de la referencia visual")
    parser.add_argument("--output-dir", default="output/generated_references")
    args = parser.parse_args()

    c1_output = json.loads(Path(args.c1).read_text(encoding="utf-8"))
    imaging_study = {"image_path": args.imagen} if args.imagen else None

    pipeline = OncoBridgePipeline(kb_path="data/knowledge_base")
    output = pipeline.run_component2(
        c1_output, imaging_study=imaging_study, device=args.device, output_dir=args.output_dir
    )
    print(json.dumps(output, indent=2, ensure_ascii=False))
