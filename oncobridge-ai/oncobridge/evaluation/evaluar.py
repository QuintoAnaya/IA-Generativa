"""
Motor de evaluacion. Corre el Componente 1 contra los 110 casos clinicos del
dataset y calcula las metricas pedidas en la seccion 5.2 del enunciado.

Metricas de Componente 1 implementadas:
  - Accuracy de Derivacion: coincidencia de `recommendation` vs `specialist_decision`.
  - Sensibilidad (Recall): de los casos que SI necesitan imagen (ground truth),
    % que el sistema tambien deriva.
  - Especificidad: de los casos que NO necesitan imagen, % que el sistema
    tambien descarta.
  - Precision de GT Match: % de casos donde el gt_id de mayor `match_probability`
    esta entre los `correct_gt_ids` (o `acceptable_secondary_gt_ids`) esperados.
  - Calibracion de GT Probability: correlacion (Pearson) entre `match_probability`
    del gt top y si el match fue efectivamente correcto (1/0) — una forma simple
    y estandar de medir calibracion sin necesitar bins de probabilidad con pocos
    datos por bin.
  - Eficiencia de Tokens: promedio de `total_tokens` por caso, y promedio de
    `gt_entries_in_context` / `retrieved_gt_entries` (cuanto se comprimio el
    contexto respecto a lo recuperado).

Uso:
    python scripts/run_evaluacion.py
"""

from __future__ import annotations

import json
import statistics
from pathlib import Path

from oncobridge.pipeline import OncoBridgePipeline


def _pearson(xs: list, ys: list) -> float:
    if len(xs) < 2 or len(set(xs)) < 2 or len(set(ys)) < 2:
        return float("nan")
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    std_x = (sum((x - mean_x) ** 2 for x in xs)) ** 0.5
    std_y = (sum((y - mean_y) ** 2 for y in ys)) ** 0.5
    if std_x == 0 or std_y == 0:
        return float("nan")
    return cov / (std_x * std_y)


def load_cases(dataset_dir: str, manifest: str = None) -> list:
    """Carga los casos del dataset. Con `manifest`, restringe a los case_id de
    esa particion (ver scripts/split_dataset.py)."""
    dataset_dir = Path(dataset_dir)
    index = json.loads((dataset_dir / "index.json").read_text(encoding="utf-8"))
    allowed = None
    if manifest:
        allowed = set(json.loads(Path(manifest).read_text(encoding="utf-8"))["case_ids"])
    cases = []
    for c in index["cases"]:
        if allowed is not None and c["case_id"] not in allowed:
            continue
        case_dir = dataset_dir / "clinical_cases" / c["case_id"]
        input_data = json.loads((case_dir / "input.json").read_text(encoding="utf-8"))
        expected = json.loads((case_dir / "expected_output.json").read_text(encoding="utf-8"))
        cases.append({"case_id": c["case_id"], "category": c["category"], "input": input_data, "expected": expected})
    return cases


def evaluate(kb_path: str = "data/knowledge_base", dataset_dir: str = "data/eval_dataset",
             verbose: bool = True, manifest: str = None, pipeline=None) -> dict:
    pipeline = pipeline or OncoBridgePipeline(kb_path=kb_path)
    cases = load_cases(dataset_dir, manifest)

    rows = []
    for case in cases:
        output = pipeline.run_component1(case["input"])
        rows.append({"case": case, "output": output})
        if verbose:
            print(f"  {case['case_id']} ({case['category']:8s}) -> "
                  f"{output['recommendation']:28s} (esperado: {case['expected']['specialist_decision']})")

    # --- Accuracy de derivacion (recommendation vs specialist_decision) ---
    correct_recommendation = sum(
        1 for r in rows if r["output"]["recommendation"] == r["case"]["expected"]["specialist_decision"]
    )
    accuracy_derivacion = correct_recommendation / len(rows)

    # --- Sensibilidad / especificidad (necesita imagen si o no) ---
    tp = fn = tn = fp = 0
    for r in rows:
        needed_gt = r["case"]["expected"]["imaging_needed_ground_truth"]
        derived = r["output"]["recommendation"] == "DERIVAR_A_IMAGEN"
        if needed_gt and derived:
            tp += 1
        elif needed_gt and not derived:
            fn += 1
        elif not needed_gt and not derived:
            tn += 1
        elif not needed_gt and derived:
            fp += 1
    sensibilidad = tp / (tp + fn) if (tp + fn) else float("nan")
    especificidad = tn / (tn + fp) if (tn + fp) else float("nan")

    # --- Precision de GT match (top-1 dentro de correct + secundarios aceptables) ---
    gt_match_hits = 0
    gt_match_evaluable = 0
    calib_probs, calib_hits = [], []
    for r in rows:
        expected = r["case"]["expected"]
        correct_ids = set(expected.get("correct_gt_ids", []))
        acceptable_ids = correct_ids | set(expected.get("acceptable_secondary_gt_ids", []))
        matched = r["output"]["matched_ground_truths"]
        if not correct_ids:
            continue  # caso no conclusivo esperado, no aplica precision de GT match
        gt_match_evaluable += 1
        if matched:
            top = matched[0]
            hit = top["gt_id"] in acceptable_ids
            gt_match_hits += int(hit)
            calib_probs.append(top["match_probability"])
            calib_hits.append(1.0 if top["gt_id"] in correct_ids else 0.0)
    precision_gt_match = gt_match_hits / gt_match_evaluable if gt_match_evaluable else float("nan")
    calibracion = _pearson(calib_probs, calib_hits)

    # --- Conclusive accuracy (bonus, no pedido explicitamente pero relevante) ---
    conclusive_correct = sum(
        1 for r in rows if r["output"]["conclusive"] == r["case"]["expected"]["conclusive_ground_truth"]
    )
    conclusive_accuracy = conclusive_correct / len(rows)

    # --- Eficiencia de tokens ---
    total_tokens = [r["output"]["token_usage"]["total_tokens"] for r in rows]
    retrieved = [r["output"]["token_usage"]["retrieved_gt_entries"] for r in rows]
    in_context = [r["output"]["token_usage"]["gt_entries_in_context"] for r in rows]
    avg_tokens = statistics.mean(total_tokens)
    avg_retrieved = statistics.mean(retrieved)
    avg_in_context = statistics.mean(in_context)

    # --- Desglose por categoria (TP/TN/FP/FN/COMPLEX) ---
    by_category = {}
    for r in rows:
        cat = r["case"]["category"]
        by_category.setdefault(cat, {"total": 0, "recommendation_correcta": 0})
        by_category[cat]["total"] += 1
        if r["output"]["recommendation"] == r["case"]["expected"]["specialist_decision"]:
            by_category[cat]["recommendation_correcta"] += 1
    for cat, d in by_category.items():
        d["accuracy"] = d["recommendation_correcta"] / d["total"]

    # Concordancia de urgencia, solo sobre los casos que efectivamente se derivan.
    urgency_evaluable = urgency_correct = 0
    for r in rows:
        if r["output"]["recommendation"] == "DERIVAR_A_IMAGEN":
            urgency_evaluable += 1
            if r["output"]["urgency"] == r["case"]["expected"]["urgency_ground_truth"]:
                urgency_correct += 1
    urgency_accuracy = urgency_correct / urgency_evaluable if urgency_evaluable else float("nan")

    results = {
        "n_casos": len(rows),
        "manifest": manifest or "dataset completo",
        "urgency_accuracy": urgency_accuracy,
        "accuracy_derivacion": accuracy_derivacion,
        "sensibilidad": sensibilidad,
        "especificidad": especificidad,
        "precision_gt_match": precision_gt_match,
        "calibracion_pearson": calibracion,
        "conclusive_accuracy": conclusive_accuracy,
        "eficiencia_tokens": {
            "promedio_total_tokens_por_caso": avg_tokens,
            "promedio_gt_recuperados_por_rag": avg_retrieved,
            "promedio_gt_en_contexto_del_llm": avg_in_context,
            "compresion_contexto_pct": (
                100 * (1 - avg_in_context / avg_retrieved) if avg_retrieved else 0.0
            ),
        },
        "confusion_derivacion": {"tp": tp, "fn": fn, "tn": tn, "fp": fp},
        "por_categoria": by_category,
    }
    return results


def print_report(results: dict):
    print("\n" + "=" * 70)
    print("REPORTE DE EVALUACION - OncoBridge AI - Componente 1")
    print("=" * 70)
    print(f"Particion:                    {results['manifest']}")
    print(f"Casos evaluados:              {results['n_casos']}")
    print(f"Accuracy de derivacion:       {results['accuracy_derivacion']:.3f}")
    print(f"Sensibilidad (recall):        {results['sensibilidad']:.3f}")
    print(f"Especificidad:                {results['especificidad']:.3f}")
    print(f"Precision de GT match (top1): {results['precision_gt_match']:.3f}")
    print(f"Calibracion (pearson r):      {results['calibracion_pearson']:.3f}")
    print(f"Accuracy de 'conclusive':     {results['conclusive_accuracy']:.3f}")
    print(f"Concordancia de urgencia:     {results['urgency_accuracy']:.3f}")
    print("-" * 70)
    tok = results["eficiencia_tokens"]
    print(f"Tokens totales promedio/caso: {tok['promedio_total_tokens_por_caso']:.0f}")
    print(f"GT recuperados por RAG (avg): {tok['promedio_gt_recuperados_por_rag']:.1f}")
    print(f"GT pasados al LLM (avg):      {tok['promedio_gt_en_contexto_del_llm']:.1f}")
    print(f"Compresion de contexto:       {tok['compresion_contexto_pct']:.1f}%")
    print("-" * 70)
    print("Matriz de confusion (derivar a imagen si/no):")
    cm = results["confusion_derivacion"]
    print(f"  TP={cm['tp']}  FN={cm['fn']}  TN={cm['tn']}  FP={cm['fp']}")
    print("-" * 70)
    print("Accuracy por categoria del dataset:")
    for cat, d in sorted(results["por_categoria"].items()):
        print(f"  {cat:10s} n={d['total']:3d}  accuracy={d['accuracy']:.3f}")
    print("=" * 70)


if __name__ == "__main__":
    results = evaluate()
    print_report(results)
