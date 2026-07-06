"""
CLI - Componente 2 (radiologo). Corre un estudio de ejemplo.

Uso:
    python scripts/run_componente2.py
    python scripts/run_componente2.py --imagen /ruta/a/estudio.dcm   # modo imagen real (opcional)
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse, json
from oncobridge.pipeline import OncoBridgePipeline
from oncobridge.utils.schemas import PacienteInput, EstudioImagenInput

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--imagen", default=None, help="ruta opcional a una imagen real (DICOM/PNG/JPG)")
    args = ap.parse_args()

    pipe = OncoBridgePipeline()
    print(f"[Modo LLM: {pipe.llm.modo}]\n")

    # primero corremos el C1 para tener el contexto-puente
    paciente = PacienteInput(
        paciente_id="DEMO", edad=64, sexo="M",
        motivo_consulta="tos con sangre",
        historia_clinica="fumador, EPOC, perdida de peso",
        sintomas_actuales=["tos persistente", "hemoptisis", "perdida de peso"],
        factores_riesgo=["tabaquismo"],
    )
    salida_c1 = pipe.c1.procesar(paciente)

    estudio = EstudioImagenInput(
        estudio_id="DEMO-TC", modalidad="TC de torax", region_anatomica="torax",
        hallazgos_estructurados=["nodulo espiculado en lobulo superior", "linfadenopatia mediastinal"],
        ruta_imagen=args.imagen,
    )
    salida = pipe.c2.procesar(estudio, contexto_c1=salida_c1)
    print(json.dumps(salida.to_dict(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
