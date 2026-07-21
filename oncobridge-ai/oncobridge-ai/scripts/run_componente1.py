"""
Corre el Componente 1 (oncologo) sobre un caso de ejemplo o un input.json propio.

Uso:
    python scripts/run_componente1.py
    python scripts/run_componente1.py --caso data/eval_dataset/clinical_cases/case_001/input.json
    python scripts/run_componente1.py --caso mi_paciente.json
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oncobridge.pipeline import OncoBridgePipeline

EJEMPLO_POSITIVO = {
    "patient_id": "PAT-DEMO-01",
    "demographics": {"age": 63, "sex": "M", "family_history": ["carcinoma_renal", "hipertension"]},
    "current_symptoms": [
        "hematuria macroscopica intermitente 3 semanas",
        "dolor lumbar izquierdo persistente",
        "masa palpable en flanco izquierdo",
    ],
    "medical_history": [
        {"date": "2015-04", "event": "Hipertension arterial en tratamiento."},
        {"date": "2021-03", "event": "Tabaquismo 30 paquetes-ano."},
    ],
    "current_labs": {"hemoglobina": 10.8, "LDH": 320, "creatinina": 1.3},
}

EJEMPLO_NEGATIVO = {
    "patient_id": "PAT-DEMO-02",
    "demographics": {"age": 29, "sex": "F", "family_history": []},
    "current_symptoms": ["chequeo de rutina, sin sintomas"],
    "medical_history": [],
    "current_labs": {"hemograma": "normal"},
}

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--caso", type=str, default=None, help="Path a un input.json")
    parser.add_argument("--ejemplo", choices=["pos", "neg"], default="pos")
    args = parser.parse_args()

    if args.caso:
        patient = json.loads(Path(args.caso).read_text(encoding="utf-8"))
    else:
        patient = EJEMPLO_POSITIVO if args.ejemplo == "pos" else EJEMPLO_NEGATIVO

    pipeline = OncoBridgePipeline(kb_path="data/knowledge_base")
    output = pipeline.run_component1(patient)
    print(json.dumps(output, indent=2, ensure_ascii=False))
