from __future__ import annotations

import re

URGENCY_WEIGHTS = {"alta": 1.00, "media": 0.65, "baja": 0.35, "ninguna": 0.00}

W_MATCH = 0.60
W_URGENCY = 0.25
W_BASE_PROB = 0.15

    code = (icd_10 or "").strip().upper()
    if not code:
        return 0.5
    letter = code[0]
    if letter == "C":
        return 1.00  # neoplasia maligna (capitulo C00-C97)
    if letter == "D":
        m = re.match(r"D(\d+)", code)
        if m:
            num = int(m.group(1))
            if 0 <= num <= 9:
                return 0.85   # D00-D09: neoplasia in situ
            if 10 <= num <= 36:
                return 0.55   # D10-D36: neoplasia benigna
            if 37 <= num <= 48:
                return 0.75   # D37-D48: comportamiento incierto/desconocido
        return 0.65
    return 0.45  # condicion no neoplasica (infecciosa/inflamatoria/otra)

THRESHOLD_DERIVAR = 0.50
THRESHOLD_SEGUIMIENTO = 0.25
# Umbral especifico para hipotesis no malignas: exige mas evidencia antes de
# derivar cuando la condicion principal no es una neoplasia maligna.
THRESHOLD_BENIGN_NO_REFERRAL = 0.55


def score_matched_gt(match_probability: float, urgency_level: str, base_probability: float,
                      icd_10: str = "") -> float:
    peso_u = URGENCY_WEIGHTS.get(urgency_level, 0.5)
    base_score = W_MATCH * match_probability + W_URGENCY * peso_u + W_BASE_PROB * base_probability
    return malignancy_weight(icd_10) * base_score


def compute_imaging_needed_probability(matched: list) -> float:
    """`matched` es una lista de dicts con keys: match_probability, urgency_level,
    base_probability, icd_10.
    """
    if not matched:
        return 0.0

    scores = [
        score_matched_gt(
            m["match_probability"], m["urgency_level"], m["base_probability"], m.get("icd_10", "")
        )
        for m in matched
    ]
    scores.sort(reverse=True)
    top = scores[0]
    secondary_support = sum(1 for s in scores[1:] if s > 0.35)
    boost = min(0.10, 0.05 * secondary_support)
    return max(0.0, min(1.0, top + boost))


def decide_recommendation(conclusive: bool, imaging_needed_probability: float,
                          top_urgency: str, top_icd_10: str = "") -> dict:
    if not conclusive:
        return {"recommendation": "SIN_ELEMENTOS_PARA_EVALUAR", "urgency": "ninguna"}

    is_malignant = (top_icd_10 or "").strip().upper().startswith("C")

    if not is_malignant and imaging_needed_probability < THRESHOLD_BENIGN_NO_REFERRAL:
        return {"recommendation": "NO_DERIVAR", "urgency": "ninguna"}

    if imaging_needed_probability >= THRESHOLD_DERIVAR:
        return {"recommendation": "DERIVAR_A_IMAGEN", "urgency": top_urgency or "media"}

    if imaging_needed_probability >= THRESHOLD_SEGUIMIENTO:
        return {"recommendation": "SEGUIMIENTO_CLINICO", "urgency": "baja"}

    return {"recommendation": "NO_DERIVAR", "urgency": "ninguna"}


def load_thresholds(path: str) -> bool:
    import json
    from pathlib import Path

    global THRESHOLD_DERIVAR, THRESHOLD_SEGUIMIENTO, THRESHOLD_BENIGN_NO_REFERRAL
    p = Path(path)
    if not p.exists():
        return False
    payload = json.loads(p.read_text(encoding="utf-8"))
    cfg = payload.get("best_thresholds", payload)
    THRESHOLD_DERIVAR = cfg.get("threshold_derivar", THRESHOLD_DERIVAR)
    THRESHOLD_SEGUIMIENTO = cfg.get("threshold_seguimiento", THRESHOLD_SEGUIMIENTO)
    THRESHOLD_BENIGN_NO_REFERRAL = cfg.get("threshold_benign_no_referral", THRESHOLD_BENIGN_NO_REFERRAL)
    return True
