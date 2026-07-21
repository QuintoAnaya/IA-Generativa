"""
Componente 1 - Analisis clinico (perfil oncologo).

Orden de ejecucion:

  1. Recuperacion de hipotesis contra la base de conocimiento (RAG, sin LLM).
  2. Calibracion de `match_probability` por entrada.
  3. Calculo de `imaging_needed_probability` con la formula documentada en
     scoring.py, y derivacion de `recommendation` y `urgency` por reglas.
  4. Redaccion del texto en lenguaje natural, unico punto donde interviene el LLM.

La separacion entre los pasos 1-3 y el paso 4 es la decision de diseno central
del sistema: toda la logica con consecuencia clinica queda resuelta por codigo
deterministico y auditable antes de que el modelo generativo reciba nada. El LLM
no puede modificar un gt_id, una probabilidad ni una recomendacion; solo redacta
sobre valores ya cerrados.
"""

from __future__ import annotations

from oncobridge.knowledge.knowledge_base import KnowledgeBase, GroundTruthEntry, flatten
from oncobridge.components import scoring
from oncobridge.utils.llm_client import GeminiClient
from oncobridge.utils.schemas import (
    PatientInput,
    Component1Output,
    MatchedGroundTruth,
    RadiologistInstructions,
    ImagingLocation,
    TokenUsage,
)

# Valores por defecto. Se sobrescriben con los calibrados en train
# (artifacts/best_thresholds.json) cuando ese archivo existe.
MATCH_THRESHOLD = 0.10
MAX_HYPOTHESES = 3


def _patient_searchable_text(patient: PatientInput) -> str:
    return flatten([
        patient.current_symptoms,
        patient.demographics.get("family_history"),
        [ev.get("event", "") for ev in patient.medical_history],
    ])


def _calibrate_match_probability(relevance: float, base_probability: float) -> float:
    """Combina la relevancia absoluta del retrieval con la probabilidad a priori
    de la entrada.

    La relevancia se toma en escala absoluta y no relativa al mejor candidato
    del caso. Normalizar contra el maximo del propio caso hace que, en pacientes
    sin patologia, el candidato menos malo quede con probabilidad alta aunque la
    evidencia sea nula, porque siempre existe un maximo.
    """
    p = 0.62 * min(1.0, relevance / 0.45) + 0.38 * base_probability
    return max(0.02, min(0.97, p))


def _build_radiologist_instructions(entry: GroundTruthEntry) -> RadiologistInstructions:
    guidance = entry.radiologist_guidance
    loc = guidance.get("imaging_location", {}) or {}
    imaging_location = ImagingLocation(
        body_region=loc.get("body_region", ""),
        anatomical_landmarks=loc.get("anatomical_landmarks", ""),
        bilateral_comparison_required=bool(loc.get("bilateral_comparison_required", False)),
        priority_zones=list(loc.get("priority_zones", []) or []),
        positioning_notes=loc.get("positioning_notes", ""),
    )
    return RadiologistInstructions(
        suggested_modalities=list(guidance.get("modality_priority", []) or []),
        views_recommended=list(guidance.get("views_recommended", []) or []),
        imaging_location=imaging_location,
        clinical_context_for_radiologist=(
            f"Hipotesis a descartar: {entry.icd_10_description} ({entry.icd_10}). "
            f"Hallazgos esperados: {guidance.get('expected_imaging_findings', 'no especificados en la base')}"
        ),
        meddiffusion_reference_prompt=guidance.get("meddiffusion_prompt", ""),
        meddiffusion_negative_prompt=guidance.get("meddiffusion_negative_prompt", ""),
        reference_images_note=guidance.get(
            "image_generation_notes",
            "Referencia visual orientativa del patron esperado. No corresponde al paciente.",
        ),
    )


def _summary_text(patient: PatientInput) -> str:
    demo = patient.demographics
    symptoms = "; ".join(patient.current_symptoms[:3]) or "sin sintomas consignados"
    return (
        f"Paciente {patient.patient_id}, {demo.get('age', 'edad no consignada')} anios, "
        f"sexo {demo.get('sex', 'no consignado')}. Motivo de consulta: {symptoms}."
    )


def _reasoning_text(conclusive: bool, n_matches: int, imaging_prob: float, recommendation: str) -> str:
    if not conclusive:
        return (
            "No se recupero ninguna hipotesis de la base de conocimiento con evidencia "
            "suficiente para sostenerla. El resultado no indica una falla del analisis: "
            "significa que los datos aportados no orientan a ninguna de las condiciones "
            "cubiertas por la base. Corresponde evaluacion clinica profesional si los "
            "sintomas persisten o aparecen signos de alarma."
        )
    return (
        f"Se recuperaron {n_matches} hipotesis compatibles, ordenadas por la evidencia "
        f"clinica que las sostiene. La probabilidad de requerir diagnostico por imagenes "
        f"resulto {imaging_prob:.2f}, lo que determina la recomendacion {recommendation}. "
        "El resultado se emite para revision profesional y no constituye un diagnostico."
    )


def run_component1(patient: PatientInput, kb: KnowledgeBase, llm: GeminiClient) -> Component1Output:
    patient_text = _patient_searchable_text(patient)
    age = patient.demographics.get("age")
    retrieval = kb.retrieve(patient_text, patient.current_labs, age=age)

    selected = [r for r in retrieval["in_context"] if r.relevance > MATCH_THRESHOLD][:MAX_HYPOTHESES]
    conclusive = len(selected) > 0

    matched_ground_truths = []
    for result in selected:
        entry = kb.get(result.gt_id)
        matched_ground_truths.append(
            MatchedGroundTruth(
                gt_id=entry.gt_id,
                icd_10=entry.icd_10,
                icd_10_description=entry.icd_10_description,
                match_probability=_calibrate_match_probability(result.relevance, entry.base_probability),
                match_rationale="; ".join(result.evidence),
                radiologist_instructions=_build_radiologist_instructions(entry),
            )
        )
    matched_ground_truths.sort(key=lambda m: m.match_probability, reverse=True)

    imaging_needed_probability = scoring.compute_imaging_needed_probability([
        {
            "match_probability": m.match_probability,
            "urgency_level": kb.get(m.gt_id).urgency_level,
            "base_probability": kb.get(m.gt_id).base_probability,
            "icd_10": kb.get(m.gt_id).icd_10,
        }
        for m in matched_ground_truths
    ])
    top_urgency = kb.get(matched_ground_truths[0].gt_id).urgency_level if matched_ground_truths else "ninguna"
    top_icd = kb.get(matched_ground_truths[0].gt_id).icd_10 if matched_ground_truths else ""
    decision = scoring.decide_recommendation(
        conclusive, imaging_needed_probability, top_urgency, top_icd
    )

    # Redaccion en lenguaje natural. Si no hay API key configurada, el cliente
    # devuelve el texto de respaldo sin fallar (ver utils/llm_client.py).
    summary_fallback = _summary_text(patient)
    summary_resp = llm.generate(
        "Reformula el siguiente resumen clinico en dos oraciones, en espanol neutro, "
        "sin agregar ningun dato que no este presente:\n" + summary_fallback,
        summary_fallback,
    )

    reasoning_fallback = _reasoning_text(
        conclusive, len(matched_ground_truths), imaging_needed_probability, decision["recommendation"]
    )
    reasoning_resp = llm.generate(
        "Reformula el siguiente razonamiento clinico en un parrafo breve, en espanol neutro. "
        "No modifiques la recomendacion, las probabilidades ni el numero de hipotesis:\n"
        + reasoning_fallback,
        reasoning_fallback,
    )

    prompt_tokens = summary_resp.prompt_tokens + reasoning_resp.prompt_tokens
    completion_tokens = summary_resp.completion_tokens + reasoning_resp.completion_tokens

    return Component1Output(
        patient_id=patient.patient_id,
        clinical_summary=summary_resp.text,
        matched_ground_truths=matched_ground_truths,
        imaging_needed_probability=imaging_needed_probability,
        reasoning=reasoning_resp.text,
        recommendation=decision["recommendation"],
        urgency=decision["urgency"],
        conclusive=conclusive,
        token_usage=TokenUsage(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            model=summary_resp.model,
            retrieved_gt_entries=retrieval["retrieved_gt_entries"],
            gt_entries_in_context=retrieval["gt_entries_in_context"],
        ),
    )
