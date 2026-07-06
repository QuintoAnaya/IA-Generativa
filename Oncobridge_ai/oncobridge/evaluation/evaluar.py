"""
Motor de evaluacion de OncoBridge AI.

Corre el dataset de casos contra el pipeline y calcula metricas:
  - Derivacion a imagen: precision, recall, F1, accuracy (positivo=requiere imagen).
  - Acierto de hipotesis diagnostica principal (top-1) en casos positivos.
  - Acierto de nivel de urgencia (triage).
  - Matriz de confusion de la decision de imagen.

El "ground truth" viene del dataset (data/eval_dataset/casos_evaluacion.json).
"""

import json
from pathlib import Path
from oncobridge.pipeline import OncoBridgePipeline
from oncobridge.utils.schemas import PacienteInput, EstudioImagenInput
import unicodedata


def _norm(t: str) -> str:
    t = (t or "").lower().strip()
    t = unicodedata.normalize("NFKD", t)
    return "".join(c for c in t if not unicodedata.combining(c))


def _dict_a_paciente(d: dict) -> PacienteInput:
    return PacienteInput(
        paciente_id=d["paciente_id"], edad=d["edad"], sexo=d["sexo"],
        motivo_consulta=d["motivo_consulta"], historia_clinica=d["historia_clinica"],
        sintomas_actuales=d.get("sintomas_actuales", []),
        factores_riesgo=d.get("factores_riesgo", []),
        biomarcadores=d.get("biomarcadores", {}),
    )


def _dict_a_estudio(d: dict | None) -> EstudioImagenInput | None:
    if not d:
        return None
    return EstudioImagenInput(
        estudio_id=d["estudio_id"], modalidad=d["modalidad"],
        region_anatomica=d["region_anatomica"],
        hallazgos_estructurados=d.get("hallazgos_estructurados", []),
        ruta_imagen=d.get("ruta_imagen"),
    )


def evaluar(ruta_dataset: str | Path | None = None, forzar_mock: bool = False, verbose: bool = True) -> dict:
    if ruta_dataset is None:
        ruta_dataset = Path(__file__).resolve().parents[2] / "data" / "eval_dataset" / "casos_evaluacion.json"
    with open(ruta_dataset, "r", encoding="utf-8") as f:
        dataset = json.load(f)

    pipe = OncoBridgePipeline(forzar_mock=forzar_mock)

    # contadores para la decision de imagen
    tp = fp = tn = fn = 0
    # aciertos diagnostico y urgencia (solo en positivos)
    dx_correctos = dx_total = 0
    urg_correctos = urg_total = 0
    detalle = []

    for caso in dataset["casos"]:
        paciente = _dict_a_paciente(caso["paciente"])
        estudio = _dict_a_estudio(caso.get("estudio"))
        gt = caso["ground_truth"]

        res = pipe.run(paciente, estudio)
        c1 = res.salida_c1

        pred_imagen = c1.requiere_imagen
        esp_imagen = gt["requiere_imagen_esperado"]

        # matriz de confusion (positivo = requiere imagen)
        if pred_imagen and esp_imagen:
            tp += 1
        elif pred_imagen and not esp_imagen:
            fp += 1
        elif not pred_imagen and not esp_imagen:
            tn += 1
        else:
            fn += 1

        dx_ok = urg_ok = None
        if esp_imagen and gt["tipo_cancer_esperado"] != "ninguno":
            dx_total += 1
            pred_dx = c1.hipotesis[0].tipo_cancer if c1.hipotesis else ""
            dx_ok = _norm(pred_dx) == _norm(gt["tipo_cancer_esperado"])
            dx_correctos += int(dx_ok)

            urg_total += 1
            urg_ok = _norm(c1.urgencia_triage) == _norm(gt["urgencia_esperada"])
            urg_correctos += int(urg_ok)

        detalle.append({
            "caso_id": caso["caso_id"], "tipo": caso["tipo"],
            "imagen_pred": pred_imagen, "imagen_esp": esp_imagen,
            "dx_pred": (c1.hipotesis[0].tipo_cancer if c1.hipotesis else "-"),
            "dx_esp": gt["tipo_cancer_esperado"],
            "dx_ok": dx_ok, "urg_ok": urg_ok,
        })

    # metricas de derivacion a imagen
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    accuracy = (tp + tn) / (tp + tn + fp + fn) if (tp + tn + fp + fn) else 0.0

    resultados = {
        "modo_llm": res.modo_llm,
        "n_casos": len(dataset["casos"]),
        "derivacion_imagen": {
            "precision": round(precision, 3), "recall": round(recall, 3),
            "f1": round(f1, 3), "accuracy": round(accuracy, 3),
            "matriz_confusion": {"TP": tp, "FP": fp, "TN": tn, "FN": fn},
        },
        "diagnostico_top1": {
            "aciertos": dx_correctos, "total": dx_total,
            "accuracy": round(dx_correctos / dx_total, 3) if dx_total else 0.0,
        },
        "urgencia_triage": {
            "aciertos": urg_correctos, "total": urg_total,
            "accuracy": round(urg_correctos / urg_total, 3) if urg_total else 0.0,
        },
        "detalle_por_caso": detalle,
    }

    if verbose:
        _imprimir(resultados)
    return resultados


def _imprimir(r: dict):
    print("=" * 68)
    print("  RESULTADOS DE EVALUACION - OncoBridge AI")
    print("=" * 68)
    print(f"  Modo LLM: {r['modo_llm']}   |   Casos evaluados: {r['n_casos']}")
    print("-" * 68)
    di = r["derivacion_imagen"]
    mc = di["matriz_confusion"]
    print("  DERIVACION A IMAGEN (positivo = requiere imagen)")
    print(f"    Precision: {di['precision']:.3f}   Recall: {di['recall']:.3f}   "
          f"F1: {di['f1']:.3f}   Accuracy: {di['accuracy']:.3f}")
    print(f"    Matriz de confusion -> TP={mc['TP']}  FP={mc['FP']}  TN={mc['TN']}  FN={mc['FN']}")
    print("-" * 68)
    dx = r["diagnostico_top1"]
    print(f"  DIAGNOSTICO TOP-1 (casos positivos): {dx['aciertos']}/{dx['total']} "
          f"= {dx['accuracy']:.3f}")
    ur = r["urgencia_triage"]
    print(f"  URGENCIA / TRIAGE (casos positivos): {ur['aciertos']}/{ur['total']} "
          f"= {ur['accuracy']:.3f}")
    print("-" * 68)
    print("  DETALLE POR CASO:")
    print(f"    {'Caso':<6}{'Tipo':<10}{'Img pred/esp':<16}{'Dx OK':<7}{'Urg OK':<7}")
    for d in r["detalle_por_caso"]:
        img = f"{str(d['imagen_pred'])[0]}/{str(d['imagen_esp'])[0]}"
        dxok = "-" if d["dx_ok"] is None else ("si" if d["dx_ok"] else "NO")
        urok = "-" if d["urg_ok"] is None else ("si" if d["urg_ok"] else "NO")
        print(f"    {d['caso_id']:<6}{d['tipo']:<10}{img:<16}{dxok:<7}{urok:<7}")
    print("=" * 68)


if __name__ == "__main__":
    evaluar()
