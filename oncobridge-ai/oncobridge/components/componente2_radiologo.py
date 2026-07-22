from __future__ import annotations

import re
from pathlib import Path

from oncobridge.knowledge.knowledge_base import KnowledgeBase
from oncobridge.utils.llm_client import GeminiClient
from oncobridge.utils.image_gen import generate_reference
from oncobridge.utils.schemas import (
    Component1Output,
    Component2Output,
    RegionOfInterest,
    GeneratedReference,
    TokenUsageC2,
)


def _empty_output(patient_id: str) -> Component2Output:
    return Component2Output(
        patient_id=patient_id,
        segmentation={"regions_of_interest": []},
        findings=(
            "El Componente 1 no sostuvo ninguna hipótesis, de modo que no hay pregunta "
            "clínica que orientar la lectura del estudio."
        ),
        classification="sin_hallazgos",
        confidence=0.0,
        final_recommendation=(
            "Sin hipótesis de origen. Corresponde criterio del profesional solicitante."
        ),
        next_steps=[],
        token_usage=TokenUsageC2(0, 0, 0, "n/a"),
        generated_radiology_reference=GeneratedReference(
            image_path="", model="", gt_id="", prompt="", negative_prompt="",
            device="", limitation="No se genero referencia: no hay hipotesis de origen.",
        ),
    )


def _reference_size_mm(expected_findings_text: str):
    if not expected_findings_text:
        return None
    text = expected_findings_text.lower()

    # cm: admite rango "4-6 cm" o valor unico "3 cm" / "2,5 cm"
    m_cm = re.search(r"(\d+(?:[.,]\d+)?)\s*(?:-\s*\d+(?:[.,]\d+)?\s*)?cm", text)
    if m_cm:
        value = float(m_cm.group(1).replace(",", "."))
        return round(value * 10.0, 1)

    m_mm = re.search(r"(\d+(?:[.,]\d+)?)\s*mm", text)
    if m_mm:
        return round(float(m_mm.group(1).replace(",", ".")), 1)

    return None


def _region_from_real_image(entry, location, image_path, llm):
    return RegionOfInterest(
        id="ROI-01",
        location=location.anatomical_landmarks or location.body_region,
        size_mm=None,
        shape="a evaluar sobre la imagen",
        margins="a evaluar sobre la imagen",
        density="a evaluar sobre la imagen",
        measurement_source="imagen_real",
    )


def run_component2(c1_output: Component1Output, kb: KnowledgeBase, llm: GeminiClient,
                   imaging_study: dict = None, output_dir: str = "output/generated_references",
                   device: str = "auto") -> Component2Output:
    if not c1_output.matched_ground_truths:
        return _empty_output(c1_output.patient_id)

    top = max(c1_output.matched_ground_truths, key=lambda m: m.match_probability)
    entry = kb.get(top.gt_id)
    guidance = entry.radiologist_guidance
    instructions = top.radiologist_instructions
    location = instructions.imaging_location

    expected_findings = guidance.get(
        "expected_imaging_findings",
        "La base de conocimiento no especifica hallazgos esperados para esta entrada.",
    )

    has_real_image = bool(
        imaging_study
        and imaging_study.get("image_path")
        and Path(imaging_study["image_path"]).exists()
    )

    reference_meta = generate_reference(
        prompt=instructions.meddiffusion_reference_prompt or entry.icd_10_description,
        negative_prompt=instructions.meddiffusion_negative_prompt,
        out_dir=output_dir,
        body_region=location.body_region,
        priority_zones=location.priority_zones,
        device=device,
    )

    if has_real_image:
        roi = _region_from_real_image(entry, location, imaging_study["image_path"], llm)
        findings = (
            f"Lectura orientada por la hipótesis principal ({entry.icd_10_description}). "
            f"Patrón esperado según la base: {expected_findings} "
            "Los hallazgos definitivos surgen de la lectura del estudio por el especialista."
        )
        measurement_note = ""
    else:
        size_mm = _reference_size_mm(expected_findings)
        roi = RegionOfInterest(
            id="ROI-01",
            location=location.anatomical_landmarks or location.body_region,
            size_mm=size_mm,
            shape=_infer_shape(expected_findings),
            margins=_infer_margins(expected_findings),
            density=_infer_density(expected_findings),
            measurement_source="referencia_ground_truth",
        )
        measurement_note = (
            " El tamaño y los descriptores de la región corresponden al patrón de "
            "referencia esperado documentado en la base de conocimiento, no a una "
            "medición sobre una imagen del paciente (el dataset no incluye estudios)."
        )
        findings = (
            f"No se dispone de un estudio del paciente. Patrón esperado si la hipótesis "
            f"'{entry.icd_10_description}' es correcta: {expected_findings}"
        )

    is_malignant = entry.icd_10.strip().upper().startswith("C")
    classification = "sospechoso" if is_malignant else "probablemente_benigno"

    next_steps = ["revision_por_especialista_en_imagenes"]
    if is_malignant:
        next_steps.append("confirmacion_histologica_si_la_imagen_es_compatible")
    if entry.urgency_level == "alta":
        next_steps.append("interconsulta_oncologica_prioritaria")
    if location.bilateral_comparison_required:
        next_steps.append("comparacion_bilateral")

    recommendation_fallback = (
        f"Leer el estudio orientado a descartar {entry.icd_10_description} ({entry.icd_10}), "
        f"con atención prioritaria en {', '.join(location.priority_zones[:2]) or location.body_region}. "
        "La guía y la imagen de referencia son material orientativo y no reemplazan el informe "
        "del especialista en imágenes." + measurement_note
    )
    recommendation_resp = llm.generate(
        "Reformula la siguiente indicacion para un radiologo en dos oraciones, en espanol neutro, "
        "sin agregar hallazgos ni modificar la hipotesis:\n" + recommendation_fallback,
        recommendation_fallback,
    )

    return Component2Output(
        patient_id=c1_output.patient_id,
        segmentation={"regions_of_interest": [roi]},
        findings=findings,
        classification=classification,
        confidence=top.match_probability,
        final_recommendation=recommendation_resp.text,
        next_steps=next_steps,
        token_usage=TokenUsageC2(
            prompt_tokens=recommendation_resp.prompt_tokens,
            completion_tokens=recommendation_resp.completion_tokens,
            total_tokens=recommendation_resp.prompt_tokens + recommendation_resp.completion_tokens,
            model=recommendation_resp.model,
        ),
        generated_radiology_reference=GeneratedReference(
            image_path=reference_meta["image_path"],
            model=reference_meta["model"],
            gt_id=entry.gt_id,
            prompt=reference_meta["prompt"],
            negative_prompt=reference_meta["negative_prompt"],
            device=reference_meta["device"],
            limitation=reference_meta["limitation"],
        ),
    )


def _infer_shape(text: str) -> str:
    t = (text or "").lower()
    if "espicul" in t or "irregular" in t:
        return "irregular"
    if "bien delimitad" in t or "redondead" in t or "homogene" in t:
        return "bien_delimitada"
    return "no_especificado"


def _infer_margins(text: str) -> str:
    t = (text or "").lower()
    if "espicul" in t:
        return "espiculados"
    if "irregular" in t:
        return "irregulares"
    if "bien delimitad" in t or "bordes lisos" in t or "definid" in t:
        return "bien_definidos"
    return "no_especificado"


def _infer_density(text: str) -> str:
    t = (text or "").lower()
    if "grasa" in t or "adipos" in t:
        return "grasa"
    if "liquid" in t or "quist" in t or "baja densidad" in t:
        return "liquida_o_baja_densidad"
    if "solid" in t or "partes blandas" in t or "realce" in t:
        return "solida"
    return "no_especificado"
