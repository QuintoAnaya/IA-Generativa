"""
CLI - Flujo end-to-end. Encadena Componente 1 -> Componente 2 sobre un caso.

Uso:
    python scripts/run_pipeline.py                # caso positivo (requiere imagen)
    python scripts/run_pipeline.py --ejemplo neg  # caso negativo (se detiene en C1)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse, json
from oncobridge.pipeline import OncoBridgePipeline
from oncobridge.utils.schemas import PacienteInput, EstudioImagenInput

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ejemplo", choices=["pos", "neg"], default="pos")
    args = ap.parse_args()

    pipe = OncoBridgePipeline()
    print(f"[Modo LLM: {pipe.llm.modo}]")
    print("=" * 60)

    if args.ejemplo == "pos":
        paciente = PacienteInput(
            paciente_id="E2E-POS", edad=64, sexo="M",
            motivo_consulta="tos persistente con sangre",
            historia_clinica="fumador de 40 paquetes-ano, EPOC, perdida de peso",
            sintomas_actuales=["tos persistente", "hemoptisis", "disnea progresiva", "perdida de peso"],
            factores_riesgo=["tabaquismo"], biomarcadores={"CEA": "elevado"},
        )
        estudio = EstudioImagenInput(
            estudio_id="E2E-TC", modalidad="TC de torax", region_anatomica="torax",
            hallazgos_estructurados=["nodulo espiculado en lobulo superior", "linfadenopatia mediastinal", "sin derrame pleural"],
        )
    else:
        paciente = PacienteInput(
            paciente_id="E2E-NEG", edad=28, sexo="F",
            motivo_consulta="dolor de cabeza por estres",
            historia_clinica="sin antecedentes oncologicos",
            sintomas_actuales=["cefalea tensional ocasional"], factores_riesgo=[],
        )
        estudio = None

    res = pipe.run(paciente, estudio)

    print("\n>>> COMPONENTE 1 (Oncologo)")
    print(json.dumps(res.salida_c1.to_dict(), indent=2, ensure_ascii=False))

    if res.salida_c2:
        print("\n>>> COMPONENTE 2 (Radiologo)")
        print(json.dumps(res.salida_c2.to_dict(), indent=2, ensure_ascii=False))
    else:
        print("\n>>> El caso NO requiere derivacion a imagen. Flujo finalizado en Componente 1.")
    print("=" * 60)

if __name__ == "__main__":
    main()
