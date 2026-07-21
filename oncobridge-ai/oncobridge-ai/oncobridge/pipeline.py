"""Orquestador end-to-end: Componente 1 seguido de Componente 2."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from oncobridge.knowledge.knowledge_base import KnowledgeBase
from oncobridge.components.componente1_oncologo import run_component1
from oncobridge.components.componente2_radiologo import run_component2
from oncobridge.components import scoring
from oncobridge.utils.llm_client import GeminiClient
from oncobridge.utils.schemas import (
    PatientInput, Component1Output, MatchedGroundTruth,
    RadiologistInstructions, ImagingLocation, TokenUsage,
)

DEFAULT_THRESHOLDS_PATH = "artifacts/best_thresholds.json"


class OncoBridgePipeline:
    def __init__(self, kb_path: str = "data/knowledge_base", api_key: Optional[str] = None,
                 thresholds_path: Optional[str] = DEFAULT_THRESHOLDS_PATH):
        self.kb = KnowledgeBase.load(kb_path)
        self.llm = GeminiClient(api_key=api_key or os.environ.get("GEMINI_API_KEY"))
        self.thresholds_loaded = scoring.load_thresholds(thresholds_path) if thresholds_path else False

    def run_component1(self, patient_dict: dict) -> dict:
        return run_component1(PatientInput.from_dict(patient_dict), self.kb, self.llm).to_dict()

    def run_component2(self, component1_output_dict: dict, device: str = "auto",
                       output_dir: str = "output/generated_references") -> dict:
        c1 = _rebuild_component1_output(component1_output_dict)
        return run_component2(c1, self.kb, self.llm, output_dir=output_dir, device=device).to_dict()

    def run_end_to_end(self, patient_dict: dict, device: str = "auto") -> dict:
        c1 = self.run_component1(patient_dict)
        c2 = self.run_component2(c1, device=device)
        return {"component_1_output": c1, "component_2_output": c2}


def _rebuild_component1_output(d: dict) -> Component1Output:
    """Reconstruye el output tipado del Componente 1 desde un dict, para poder
    encadenar los componentes tanto en memoria como a partir de un JSON en disco.
    """
    matched = []
    for m in d.get("matched_ground_truths", []):
        ri = m["radiologist_instructions"]
        matched.append(MatchedGroundTruth(
            gt_id=m["gt_id"],
            icd_10=m["icd_10"],
            icd_10_description=m["icd_10_description"],
            match_probability=m["match_probability"],
            match_rationale=m["match_rationale"],
            radiologist_instructions=RadiologistInstructions(
                suggested_modalities=ri["suggested_modalities"],
                views_recommended=ri.get("views_recommended", []),
                imaging_location=ImagingLocation(**ri["imaging_location"]),
                clinical_context_for_radiologist=ri["clinical_context_for_radiologist"],
                meddiffusion_reference_prompt=ri["meddiffusion_reference_prompt"],
                meddiffusion_negative_prompt=ri["meddiffusion_negative_prompt"],
                reference_images_note=ri["reference_images_note"],
            ),
        ))
    return Component1Output(
        patient_id=d["patient_id"],
        clinical_summary=d["clinical_summary"],
        matched_ground_truths=matched,
        imaging_needed_probability=d["imaging_needed_probability"],
        reasoning=d["reasoning"],
        recommendation=d["recommendation"],
        urgency=d["urgency"],
        conclusive=d["conclusive"],
        token_usage=TokenUsage(**d["token_usage"]),
    )
