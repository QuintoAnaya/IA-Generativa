"""
CLI - Componente 1 (oncologo). Corre un caso de ejemplo o uno pasado por --json.

Uso:
    python scripts/run_componente1.py                 # caso de ejemplo (positivo)
    python scripts/run_componente1.py --ejemplo neg   # caso de ejemplo (negativo)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse, json, sys
from oncobridge.pipeline import OncoBridgePipeline
from oncobridge.utils.schemas import PacienteInput

EJEMPLOS = {
    "pos": PacienteInput(
        paciente_id="DEMO-POS", edad=64, sexo="M",
        motivo_consulta="tos persistente con sangre",
        historia_clinica="fumador de 40 paquetes-ano, EPOC, perdida de peso reciente",
        sintomas_actuales=["tos persistente", "hemoptisis", "disnea progresiva", "perdida de peso"],
        factores_riesgo=["tabaquismo"], biomarcadores={"CEA": "elevado"},
    ),
    "neg": PacienteInput(
        paciente_id="DEMO-NEG", edad=28, sexo="F",
        motivo_consulta="dolor de cabeza por estres",
        historia_clinica="sin antecedentes oncologicos, examenes normales",
        sintomas_actuales=["cefalea tensional ocasional"], factores_riesgo=[], biomarcadores={},
    ),
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ejemplo", choices=["pos", "neg"], default="pos")
    args = ap.parse_args()

    pipe = OncoBridgePipeline()
    print(f"[Modo LLM: {pipe.llm.modo}]\n")
    salida = pipe.c1.procesar(EJEMPLOS[args.ejemplo])
    print(json.dumps(salida.to_dict(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
