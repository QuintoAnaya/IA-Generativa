"""
Componente 2 - Asistencia radiologica (perfil radiologo).

El contrato del sistema (seccion 4.3 del enunciado) define que este componente
recibe el output del Componente 1 junto con el estudio de imagen del paciente y
produce un informe estructurado con regiones de interes, hallazgos, clasificacion
y recomendacion.

El dataset entregado es exclusivamente clinico: no incluye estudios de imagen de
los pacientes. El componente contempla las dos situaciones:

  1. Si el input trae una imagen real (`imaging_study.image_path` existente), se
     usa como base del informe. Esta rama queda implementada para respetar el
     contrato, aunque el dataset actual no ejerce este camino.

  2. Si no hay imagen del paciente (caso del dataset actual), el componente
     construye el informe a partir de la hipotesis principal del Componente 1 y
     genera una referencia visual sintetica del patron que el radiologo deberia
     esperar. En esta situacion, los hallazgos y la medicion no son
     observaciones sobre el paciente: son el patron de referencia que documenta
     la propia entrada de ground truth. El informe lo indica de forma explicita
     en cada campo afectado, para no presentar como medido algo que es esperado.

En ningun caso el componente inventa hallazgos: todo lo que afirma proviene de la
imagen real (cuando existe) o del campo `expected_imaging_findings` de la entrada
de ground truth (cuando no existe).
"""

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
    """Extrae un tamano de referencia en milimetros del texto de hallazgos
    esperados de la entrada de ground truth.

    El texto describe el tamano tipico de la lesion en lenguaje clinico
    ("masa > 4-6 cm", "nodulo < 3 cm", "lesion de 8 mm"). Se toma el primer
    valor numerico con unidad y se normaliza a milimetros. Cuando hay un rango
    ("4-6 cm") se toma el extremo inferior, por ser el criterio mas conservador.
    Si el texto no aporta ningun tamano, devuelve None.
    """
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
    """Construye la region de interes a partir de una imagen real del paciente.

    Rama prevista por el contrato para cuando el input trae un estudio. El
    dataset actual no ejerce este camino; se deja la estructura lista y con la
    medicion marcada como proveniente de imagen real.
    """
    # Un analisis de segmentacion real requeriria un modelo de vision entrenado
    # sobre imagen medica anotada, fuera del alcance de este prototipo. Se deja
    # la region con la localizacion de la guia y sin medicion automatica, para
    # no reportar como medido algo que no se midio.
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

    # Se busca primero una imagen real del paciente. El dataset actual no la trae,
    # de modo que en la practica se toma la segunda rama.
    has_real_image = bool(
        imaging_study
        and imaging_study.get("image_path")
        and Path(imaging_study["image_path"]).exists()
    )

    # Siempre se genera la referencia visual sintetica del patron esperado, que
    # acompana al informe como material orientativo.
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
