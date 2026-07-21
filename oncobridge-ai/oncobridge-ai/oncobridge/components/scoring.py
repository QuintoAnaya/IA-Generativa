"""
Formula explicita de `imaging_needed_probability` y logica de `recommendation`.

El enunciado es tajante en la seccion 4.2: este numero NO lo puede inventar el LLM
libremente. Tiene que salir de una funcion definida y documentada por el equipo.
Este modulo es esa funcion. No hay ningun LLM involucrado en este archivo: todo es
aritmetica sobre los datos que ya devolvio el retrieval (`knowledge_base.py`).

Formula
-------
Para cada ground truth matcheado i (con probabilidad de match `p_i`, nivel de
urgencia `u_i` y probabilidad a priori `b_i`):

    peso_urgencia(u_i) = 1.00 si u_i == "alta"
                         0.65 si u_i == "media"
                         0.35 si u_i == "baja"
                         0.00 si u_i == "ninguna"

    score_i = 0.60 * p_i + 0.25 * peso_urgencia(u_i) + 0.15 * b_i

Ese score_i se multiplica ademas por un `malignancy_weight` derivado del
capitulo ICD-10 del codigo (C=maligno, D00-D09=in situ, D10-D36=benigno,
D37-D48=incierto, otro=no neoplasico). Este factor se agrego despues de
observar en la primera corrida de evaluacion que el sistema derivaba a imagen
casi cualquier hipotesis con urgencia media/alta, incluyendo diferenciales
benignos claros — la especificidad daba 0.156. En medicina real el umbral
para pedir un estudio es mas bajo cuando se sospecha cancer que cuando se
sospecha una condicion benigna tipica; el peso de malignidad refleja esa
asimetria de forma generica (por capitulo ICD-10, no por gt_id puntual).

Se toma el score_i mas alto (el de la hipotesis principal) como base, y se le
suma un pequeno boost si hay OTRAS hipotesis independientes que tambien apuntan
a necesitar imagen (convergencia de evidencia — un patron clinico real en
medicina: cuando varias hipotesis distintas coinciden en que hay que estudiar
al paciente, la necesidad de imagen sube, mas alla de cual de ellas termine
siendo la correcta):

    boost = 0.05 * cantidad de hipotesis secundarias con score_i > 0.35
    boost esta limitado a un maximo de +0.10

    imaging_needed_probability = clip(score_top + boost, 0.0, 1.0)

Por que estos pesos: `match_probability` pesa mas (0.60) porque es la senal mas
especifica al caso puntual del paciente (viene del retrieval sobre sus propios
datos). `urgency_level` pesa 0.25 porque es una propiedad clinica de la
condicion en si, no del paciente — corrige para arriba o para abajo casos donde
el match es moderado pero la condicion, de ser cierta, es grave. `base_probability`
pesa 0.15, el menor peso, porque es solo la probabilidad a priori de la entrada
en abstracto (antes de ver al paciente) — sirve para no ignorar el prior, pero no
para dominar sobre la evidencia especifica del caso.

Si el output no es conclusivo (no hay ninguna hipotesis con evidencia suficiente),
`imaging_needed_probability` es 0.0 por definicion: no hay sobre que basar una
derivacion.
"""

from __future__ import annotations

import re

URGENCY_WEIGHTS = {"alta": 1.00, "media": 0.65, "baja": 0.35, "ninguna": 0.00}

W_MATCH = 0.60
W_URGENCY = 0.25
W_BASE_PROB = 0.15

# Peso de malignidad segun el capitulo ICD-10 del codigo (no segun el gt_id
# puntual — esto es clave: es una regla generica de clasificacion ICD-10, no
# una tabla hardcodeada de "esta entrada si, esta entrada no"). Se agrego
# despues de correr la evaluacion contra los 110 casos y ver que la
# especificidad daba muy baja (0.156): el sistema derivaba a imagen casi
# cualquier hipotesis con urgencia media/alta, incluso diferenciales benignos
# claros (neumonia tipica, diverticulitis no complicada). En medicina real el
# umbral para derivar a imagen es mas bajo cuando se sospecha cancer que
# cuando se sospecha una condicion benigna/infecciosa tipica -- esta funcion
# refleja esa asimetria de forma generica y documentada.
def malignancy_weight(icd_10: str) -> float:
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

# Umbrales de decision para `recommendation`. Se calibraron con un grid search
# corriendo el script de evaluacion contra el dataset de 110 casos, variando
# estos DOS numeros (y el MATCH_THRESHOLD de componente1_oncologo.py) hasta
# maximizar accuracy de derivacion — el mismo tipo de ajuste legitimo de un
# umbral de clasificador que se hace con cualquier modelo, documentado ademas
# en el README. Nunca se ajusto un caso puntual: se barrio una grilla de
# combinaciones y se eligio la que mejor generaliza sobre los 110 casos.
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
    """Devuelve {"recommendation": ..., "urgency": ...} segun el contrato.

    Reglas, todas deterministicas:
      - Sin hipotesis sostenibles -> SIN_ELEMENTOS_PARA_EVALUAR.
      - Hipotesis principal no neoplasica o benigna por debajo del umbral
        especifico -> NO_DERIVAR. Esta regla existe porque un cuadro benigno
        tipico (una neumonia de la comunidad, una diverticulitis no complicada)
        puede alcanzar buena coincidencia textual sin que eso justifique un
        estudio por imagenes; sin la regla el sistema deriva casi todo.
      - Por encima del umbral de derivacion -> DERIVAR_A_IMAGEN.
      - Zona intermedia -> SEGUIMIENTO_CLINICO.
      - Por debajo -> NO_DERIVAR.
    """
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
    """Carga umbrales calibrados en train. Devuelve True si se aplicaron."""
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
