"""
Contrato de inputs/outputs del sistema OncoBridge AI.

Estas clases reflejan EXACTAMENTE la estructura de JSON definida en el enunciado
(OncoBridge_AI_Assignment.md, seccion 4). Se usan dataclasses en vez de dicts sueltos
para que el contrato quede tipado, autodocumentado y sea mas dificil romperlo por error
al tocar el codigo de los componentes.

Todas las clases tienen un metodo `to_dict()` que devuelve exactamente el JSON que
espera el contrato (mismos nombres de campo, mismo anidamiento).
"""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Optional


# ---------------------------------------------------------------------------
# Valores enumerados del contrato (seccion 4.2 del enunciado)
# ---------------------------------------------------------------------------

RECOMMENDATION_VALUES = (
    "DERIVAR_A_IMAGEN",
    "NO_DERIVAR",
    "SEGUIMIENTO_CLINICO",
    "SIN_ELEMENTOS_PARA_EVALUAR",
)

URGENCY_VALUES = ("alta", "media", "baja", "ninguna")


# ---------------------------------------------------------------------------
# Input de Componente 1
# ---------------------------------------------------------------------------

@dataclass
class PatientInput:
    """Input al Componente 1. Espeja el input.json de cada caso clinico."""

    patient_id: str
    demographics: dict
    current_symptoms: list
    medical_history: list
    current_labs: dict

    @staticmethod
    def from_dict(d: dict) -> "PatientInput":
        return PatientInput(
            patient_id=d.get("patient_id", "PAT-UNKNOWN"),
            demographics=d.get("demographics", {}) or {},
            current_symptoms=d.get("current_symptoms", []) or [],
            medical_history=d.get("medical_history", []) or [],
            current_labs=d.get("current_labs", {}) or {},
        )


# ---------------------------------------------------------------------------
# Piezas del output de Componente 1
# ---------------------------------------------------------------------------

@dataclass
class ImagingLocation:
    body_region: str = ""
    anatomical_landmarks: str = ""
    bilateral_comparison_required: bool = False
    priority_zones: list = field(default_factory=list)
    positioning_notes: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class RadiologistInstructions:
    suggested_modalities: list
    views_recommended: list
    imaging_location: ImagingLocation
    clinical_context_for_radiologist: str
    meddiffusion_reference_prompt: str
    meddiffusion_negative_prompt: str
    reference_images_note: str

    def to_dict(self) -> dict:
        d = asdict(self)
        return d


@dataclass
class MatchedGroundTruth:
    gt_id: str
    icd_10: str
    icd_10_description: str
    match_probability: float
    match_rationale: str
    radiologist_instructions: RadiologistInstructions

    def to_dict(self) -> dict:
        return {
            "gt_id": self.gt_id,
            "icd_10": self.icd_10,
            "icd_10_description": self.icd_10_description,
            "match_probability": round(self.match_probability, 4),
            "match_rationale": self.match_rationale,
            "radiologist_instructions": self.radiologist_instructions.to_dict(),
        }


@dataclass
class TokenUsage:
    """Obligatorio por el contrato (seccion 4.2). Mide eficiencia de contexto."""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int
    model: str
    retrieved_gt_entries: int
    gt_entries_in_context: int

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Component1Output:
    patient_id: str
    clinical_summary: str
    matched_ground_truths: list  # list[MatchedGroundTruth]
    imaging_needed_probability: float
    reasoning: str
    recommendation: str
    urgency: str
    conclusive: bool
    token_usage: TokenUsage

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "clinical_summary": self.clinical_summary,
            "matched_ground_truths": [m.to_dict() for m in self.matched_ground_truths],
            "imaging_needed_probability": round(self.imaging_needed_probability, 4),
            "reasoning": self.reasoning,
            "recommendation": self.recommendation,
            "urgency": self.urgency,
            "conclusive": self.conclusive,
            "token_usage": self.token_usage.to_dict(),
        }


# ---------------------------------------------------------------------------
# Output de Componente 2
# ---------------------------------------------------------------------------

@dataclass
class GeneratedReference:
    """Metadatos de la referencia visual sintetica producida por el Componente 2."""
    image_path: str
    model: str
    gt_id: str
    prompt: str
    negative_prompt: str
    device: str
    limitation: str

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Component2Output:
    patient_id: str
    source_gt_id: str
    expected_findings: str
    reading_guide: dict
    generated_radiology_reference: GeneratedReference
    confidence_in_hypothesis: float
    final_recommendation: str
    next_steps: list
    token_usage: TokenUsage

    def to_dict(self) -> dict:
        return {
            "patient_id": self.patient_id,
            "source_gt_id": self.source_gt_id,
            "expected_findings": self.expected_findings,
            "reading_guide": self.reading_guide,
            "generated_radiology_reference": self.generated_radiology_reference.to_dict(),
            "confidence_in_hypothesis": round(self.confidence_in_hypothesis, 4),
            "final_recommendation": self.final_recommendation,
            "next_steps": self.next_steps,
            "token_usage": self.token_usage.to_dict(),
        }
