"""
Cliente del modelo generativo (Google Gemini).

>>> DONDE VA LA API KEY <<<
La API key NUNCA se escribe en el codigo. Se lee de una variable de entorno
llamada GEMINI_API_KEY. Para cargarla, se usa un archivo .env en la raiz del
repo (que esta bloqueado por .gitignore y NO se sube a GitHub).

Ver el archivo .env.example para el formato. El usuario debe:
  1. Copiar .env.example a .env
  2. Pegar su API key real de Gemini en .env
  3. Listo. El codigo la levanta solo.

Si no hay API key configurada, el sistema cae automaticamente a un MODO
SIMULADO (mock) determinista, para que el proyecto SIEMPRE corra end-to-end
aunque el corrector todavia no haya cargado su key.
"""

import os
import json
import hashlib

# Cargar variables de entorno desde .env si python-dotenv esta disponible.
try:
    from dotenv import load_dotenv
    from pathlib import Path
    _env_path = Path(__file__).resolve().parents[2] / ".env"
    load_dotenv(dotenv_path=_env_path)
except ImportError:
    pass  # sin dotenv, se usan las variables de entorno del sistema si existen


class LLMClient:
    """Wrapper delgado sobre Gemini con fallback a modo simulado."""

    def __init__(self, modelo: str | None = None, forzar_mock: bool = False):
        self.modelo = modelo or os.environ.get("GEMINI_MODEL", "gemini-1.5-flash")
        self.api_key = os.environ.get("GEMINI_API_KEY", "").strip()
        self.mock = forzar_mock or not self.api_key
        self._cliente = None

        if not self.mock:
            try:
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self._cliente = genai.GenerativeModel(self.modelo)
            except Exception as e:
                # Si falla la importacion o la config, caemos a mock sin romper.
                print(f"[LLMClient] No se pudo inicializar Gemini ({e}). Usando modo simulado.")
                self.mock = True

    @property
    def modo(self) -> str:
        return "SIMULADO (mock)" if self.mock else f"GEMINI ({self.modelo})"

    def generar(self, prompt: str, temperatura: float = 0.2) -> str:
        """Genera texto a partir de un prompt. En modo mock, respuesta determinista."""
        if self.mock:
            return self._generar_mock(prompt)
        try:
            import google.generativeai as genai
            resp = self._cliente.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(temperature=temperatura),
                request_options={"timeout": 30},  # evita cuelgues si la API no responde
            )
            return resp.text
        except Exception as e:
            print(f"[LLMClient] Error llamando a Gemini ({e}). Devuelvo respuesta simulada.")
            return self._generar_mock(prompt)

    def generar_json(self, prompt: str, temperatura: float = 0.2) -> dict:
        """Genera y parsea una respuesta JSON. Robusto ante fences de markdown."""
        texto = self.generar(prompt, temperatura=temperatura)
        return self._parsear_json(texto)

    # ---------------- internos ----------------

    @staticmethod
    def _parsear_json(texto: str) -> dict:
        limpio = texto.strip()
        if limpio.startswith("```"):
            # sacar fences ```json ... ```
            limpio = limpio.split("```", 2)
            limpio = limpio[1] if len(limpio) > 1 else texto
            if limpio.startswith("json"):
                limpio = limpio[4:]
            limpio = limpio.strip().rstrip("`").strip()
        try:
            return json.loads(limpio)
        except json.JSONDecodeError:
            # ultimo intento: extraer el primer bloque {...}
            inicio = limpio.find("{")
            fin = limpio.rfind("}")
            if inicio != -1 and fin != -1:
                try:
                    return json.loads(limpio[inicio:fin + 1])
                except json.JSONDecodeError:
                    pass
            return {"_error_parseo": True, "_texto_crudo": texto}

    def _generar_mock(self, prompt: str) -> str:
        """
        Respuesta simulada DETERMINISTA. No inventa diagnosticos: se limita a
        reformatear/senializar. Los componentes estan disenados para que, en
        modo mock, la logica clinica real la aporte el retrieval de la base de
        conocimiento (no el LLM). Asi el sistema es evaluable sin API key.
        """
        # Devolvemos un JSON neutro que los componentes saben interpretar.
        # El hash hace la respuesta estable para un mismo prompt.
        h = hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8]
        return json.dumps({
            "_mock": True,
            "_hash": h,
            "texto": "Respuesta generada en modo simulado (sin API key de Gemini). "
                     "La logica clinica proviene de la base de conocimiento curada."
        }, ensure_ascii=False)
