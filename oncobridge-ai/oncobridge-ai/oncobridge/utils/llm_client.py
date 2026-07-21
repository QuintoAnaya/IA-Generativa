"""
Cliente del LLM generativo (Gemini) con fallback automatico a modo simulado.

Principio de arquitectura (ver README): el LLM en este sistema SOLO redacta
texto en lenguaje natural (resumenes, justificaciones, informes) a partir de
datos que YA fueron decididos por logica deterministica (retrieval + formula
de scoring). El LLM nunca decide un gt_id, una probabilidad ni una
recomendacion — eso lo mantiene explicable y reduce el riesgo de alucinacion
en las partes del sistema que mas importan clinicamente.

Modo simulado: si no hay GEMINI_API_KEY configurada (o falla la llamada por
cualquier motivo: sin internet, cuota agotada, key invalida), el cliente cae
solo a plantillas de texto armadas con los mismos datos estructurados. Esto
garantiza que el sistema corre end-to-end siempre, incluso sin API key ni
conexion — requisito practico para que el corrector pueda levantarlo en menos
de 10 minutos sin depender de que una API externa este disponible en ese momento.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Optional


DEFAULT_MODEL = "gemini-1.5-flash"


@dataclass
class LLMResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    model: str
    simulated: bool


def _estimate_tokens(text: str) -> int:
    """Estimacion gruesa (no exacta) de tokens para el modo simulado: ~4
    caracteres por token en espanol, redondeado. Se usa solo cuando no hay
    una respuesta real de API de la cual leer el conteo real de tokens.
    """
    return max(1, round(len(text) / 4))


class GeminiClient:
    """Wrapper fino sobre google-generativeai. Si el paquete no esta instalado,
    no hay API key, o la llamada de red falla, todos los metodos devuelven
    una LLMResponse simulada en vez de levantar una excepcion — el llamador
    (componente 1 o 2) no necesita saber en que modo esta corriendo.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        self.model_name = model
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        self._client = None
        self._vision_ok = False

        if self.api_key:
            try:
                import google.generativeai as genai  # type: ignore

                genai.configure(api_key=self.api_key)
                self._client = genai.GenerativeModel(self.model_name)
                self._vision_ok = True
            except Exception:
                # cualquier problema (paquete no instalado, key invalida, etc.)
                # -> se queda en modo simulado silenciosamente.
                self._client = None

    @property
    def is_live(self) -> bool:
        return self._client is not None

    def generate(self, prompt: str, fallback_text: str) -> LLMResponse:
        """Genera texto. `fallback_text` es la respuesta en modo simulado —
        la arma el llamador con una plantilla, para que siempre tenga sentido
        clinico aunque no haya LLM real disponible.
        """
        if self._client is not None:
            try:
                result = self._client.generate_content(prompt)
                text = (result.text or "").strip() or fallback_text
                usage = getattr(result, "usage_metadata", None)
                if usage is not None:
                    return LLMResponse(
                        text=text,
                        prompt_tokens=int(getattr(usage, "prompt_token_count", 0) or _estimate_tokens(prompt)),
                        completion_tokens=int(getattr(usage, "candidates_token_count", 0) or _estimate_tokens(text)),
                        model=self.model_name,
                        simulated=False,
                    )
                return LLMResponse(
                    text=text,
                    prompt_tokens=_estimate_tokens(prompt),
                    completion_tokens=_estimate_tokens(text),
                    model=self.model_name,
                    simulated=False,
                )
            except Exception:
                pass  # cae a simulado abajo

        return LLMResponse(
            text=fallback_text,
            prompt_tokens=_estimate_tokens(prompt),
            completion_tokens=_estimate_tokens(fallback_text),
            model=f"{self.model_name} (modo simulado)",
            simulated=True,
        )

    def generate_vision(self, prompt: str, image_path: str, fallback_text: str) -> LLMResponse:
        """Analiza una imagen real (Componente 2, caso de imagen subida por el
        usuario). Requiere Gemini real y Pillow para abrir el archivo; si
        cualquiera de los dos falta, cae a modo simulado igual que `generate`.
        """
        if self._client is not None:
            try:
                from PIL import Image  # type: ignore

                img = Image.open(image_path)
                result = self._client.generate_content([prompt, img])
                text = (result.text or "").strip() or fallback_text
                return LLMResponse(
                    text=text,
                    prompt_tokens=_estimate_tokens(prompt) + 258,  # aprox. costo fijo de una imagen
                    completion_tokens=_estimate_tokens(text),
                    model=self.model_name,
                    simulated=False,
                )
            except Exception:
                pass

        return LLMResponse(
            text=fallback_text,
            prompt_tokens=_estimate_tokens(prompt),
            completion_tokens=_estimate_tokens(fallback_text),
            model=f"{self.model_name} (modo simulado)",
            simulated=True,
        )
