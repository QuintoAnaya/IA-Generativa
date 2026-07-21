"""
Componente 2 - Guia visual prospectiva (perfil radiologo).

El dataset entregado es exclusivamente clinico: no incluye estudios de imagen de
los pacientes. Por eso el componente no intenta detectar hallazgos sobre una
imagen real, tarea para la que ademas no habria forma de medir desempeno sin
mascaras anotadas por especialistas.

En su lugar el componente resuelve el problema inverso, que si es abordable con
los datos disponibles: a partir de la hipotesis principal del Componente 1
construye la guia de lectura y genera una ilustracion sintetica del patron que
el radiologo deberia esperar encontrar. El objetivo es que el estudio se lea con
la pregunta clinica ya formulada, en lugar de leerse a ciegas.

Ningun texto de este componente describe hallazgos observados: todo lo que
afirma proviene del campo `expected_imaging_findings` de la entrada de ground
truth, es decir, de conocimiento medico curado y no de una inferencia del modelo
sobre una imagen inexistente.
"""

from __future__ import annotations

from oncobridge.knowledge.knowledge_base import KnowledgeBase
from oncobridge.utils.llm_client import GeminiClient
from oncobridge.utils.image_gen import generate_reference
from oncobridge.utils.schemas import (
    Component1Output,
    Component2Output,
    GeneratedReference,
    TokenUsage,
)


def _empty_output(patient_id: str) -> Component2Output:
    return Component2Output(
        patient_id=patient_id,
        source_gt_id="",
        expected_findings="",
        reading_guide={},
        generated_radiology_reference=GeneratedReference(
            image_path="", model="", gt_id="", prompt="", negative_prompt="",
            device="", limitation="No se genero referencia: no hay hipotesis de origen.",
        ),
        confidence_in_hypothesis=0.0,
        final_recommendation=(
            "El Componente 1 no sostuvo ninguna hipotesis, de modo que no hay pregunta "
            "clinica que orientar. Corresponde criterio del profesional solicitante."
        ),
        next_steps=[],
        token_usage=TokenUsage(0, 0, 0, "n/a", 0, 0),
    )


def run_component2(c1_output: Component1Output, kb: KnowledgeBase, llm: GeminiClient,
                   output_dir: str = "output/generated_references",
                   device: str = "auto") -> Component2Output:
    if not c1_output.matched_ground_truths:
        return _empty_output(c1_output.patient_id)

    top = max(c1_output.matched_ground_truths, key=lambda m: m.match_probability)
    entry = kb.get(top.gt_id)
    guidance = entry.radiologist_guidance
    instructions = top.radiologist_instructions
    location = instructions.imaging_location

    reference_meta = generate_reference(
        prompt=instructions.meddiffusion_reference_prompt or entry.icd_10_description,
        negative_prompt=instructions.meddiffusion_negative_prompt,
        out_dir=output_dir,
        body_region=location.body_region,
        priority_zones=location.priority_zones,
        device=device,
    )

    reading_guide = {
        "suggested_modalities": instructions.suggested_modalities,
        "views_recommended": instructions.views_recommended,
        "body_region": location.body_region,
        "anatomical_landmarks": location.anatomical_landmarks,
        "priority_zones": location.priority_zones,
        "bilateral_comparison_required": location.bilateral_comparison_required,
        "positioning_notes": location.positioning_notes,
    }

    expected_findings = guidance.get(
        "expected_imaging_findings",
        "La base de conocimiento no especifica hallazgos esperados para esta entrada.",
    )

    is_malignant = entry.icd_10.strip().upper().startswith("C")
    next_steps = ["revision_por_especialista_en_imagenes"]
    if is_malignant:
        next_steps.append("confirmacion_histologica_si_la_imagen_es_compatible")
    if entry.urgency_level == "alta":
        next_steps.append("interconsulta_oncologica_prioritaria")
    if location.bilateral_comparison_required:
        next_steps.append("comparacion_bilateral")

    recommendation_fallback = (
        f"Leer el estudio orientado a descartar {entry.icd_10_description} ({entry.icd_10}), "
        f"con atencion prioritaria en {', '.join(location.priority_zones[:2]) or location.body_region}. "
        "La guia y la imagen de referencia son material orientativo y no reemplazan el informe "
        "del especialista en imagenes."
    )
    recommendation_resp = llm.generate(
        "Reformula la siguiente indicacion para un radiologo en dos oraciones, en espanol neutro, "
        "sin agregar hallazgos ni modificar la hipotesis:\n" + recommendation_fallback,
        recommendation_fallback,
    )

    return Component2Output(
        patient_id=c1_output.patient_id,
        source_gt_id=entry.gt_id,
        expected_findings=expected_findings,
        reading_guide=reading_guide,
        generated_radiology_reference=GeneratedReference(
            image_path=reference_meta["image_path"],
            model=reference_meta["model"],
            gt_id=entry.gt_id,
            prompt=reference_meta["prompt"],
            negative_prompt=reference_meta["negative_prompt"],
            device=reference_meta["device"],
            limitation=reference_meta["limitation"],
        ),
        confidence_in_hypothesis=top.match_probability,
        final_recommendation=recommendation_resp.text,
        next_steps=next_steps,
        token_usage=TokenUsage(
            prompt_tokens=recommendation_resp.prompt_tokens,
            completion_tokens=recommendation_resp.completion_tokens,
            total_tokens=recommendation_resp.prompt_tokens + recommendation_resp.completion_tokens,
            model=recommendation_resp.model,
            retrieved_gt_entries=1,
            gt_entries_in_context=1,
        ),
    )
