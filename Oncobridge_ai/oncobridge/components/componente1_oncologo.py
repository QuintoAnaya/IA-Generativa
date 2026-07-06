"""
Componente 1 - Consulta Oncologica Inicial (asistente del oncologo).

Flujo:
  1. Recibe el contexto clinico del paciente (PacienteInput).
  2. Consulta la base de conocimiento (retrieval) para recuperar las hipotesis
     diagnosticas mas compatibles.
  3. Decide si el caso requiere derivacion a estudios de imagen y con que urgencia.
  4. Usa el LLM (Gemini) para redactar la justificacion y el resumen-puente que
     recibira el radiologo (Componente 2). En modo mock, ese texto se arma con
     plantillas a partir de la base de conocimiento (sin inventar diagnosticos).

Diseno clave: la LOGICA CLINICA (que hipotesis, si requiere imagen, urgencia)
sale del retrieval sobre la base curada, NO del LLM. El LLM solo redacta. Esto
reduce el riesgo de alucinaciones en las decisiones que importan.
"""

from oncobridge.knowledge.knowledge_base import KnowledgeBase
from oncobridge.utils.llm_client import LLMClient
from oncobridge.utils.schemas import (
    PacienteInput, SalidaComponente1, HipotesisDiagnostica, DISCLAIMER_CLINICO
)

# Umbral: cuantos terminos deben coincidir para considerar una hipotesis "seria".
UMBRAL_SCORE_HIPOTESIS = 2
# Mapa de urgencia a prioridad numerica para elegir la mas alta.
_PRIORIDAD_URGENCIA = {"alta": 3, "media": 2, "baja": 1}


class ComponenteOncologo:
    def __init__(self, kb: KnowledgeBase | None = None, llm: LLMClient | None = None):
        self.kb = kb or KnowledgeBase()
        self.llm = llm or LLMClient()

    def procesar(self, paciente: PacienteInput, top_k: int = 3) -> SalidaComponente1:
        texto_clinico = paciente.a_texto_clinico()
        recuperadas = self.kb.recuperar(texto_clinico, top_k=top_k)

        # Construir hipotesis diagnosticas a partir del retrieval.
        hipotesis: list[HipotesisDiagnostica] = []
        score_total = sum(r["score"] for r in recuperadas) or 1
        for r in recuperadas:
            entrada = r["entrada"]
            prob = round(r["score"] / score_total, 3)
            justif = self._redactar_justificacion(paciente, entrada, r["razones"])
            hipotesis.append(HipotesisDiagnostica(
                tipo_cancer=entrada["tipo_cancer"],
                probabilidad=prob,
                justificacion=justif,
                kb_id=entrada["id"],
            ))

        # Decision de imagen y urgencia: basadas en la(s) hipotesis fuerte(s).
        hipotesis_fuertes = [r for r in recuperadas if r["score"] >= UMBRAL_SCORE_HIPOTESIS]
        requiere_imagen = any(r["entrada"]["requiere_imagen"] for r in hipotesis_fuertes)

        if hipotesis_fuertes:
            urgencia = max(
                (r["entrada"]["urgencia_triage"] for r in hipotesis_fuertes),
                key=lambda u: _PRIORIDAD_URGENCIA.get(u, 0),
            )
            modalidad = hipotesis_fuertes[0]["entrada"]["modalidad_imagen_sugerida"]
        else:
            urgencia = "baja"
            modalidad = ""

        resumen = self._redactar_resumen_radiologo(paciente, hipotesis_fuertes, requiere_imagen)

        return SalidaComponente1(
            paciente_id=paciente.paciente_id,
            requiere_imagen=requiere_imagen,
            urgencia_triage=urgencia,
            hipotesis=hipotesis,
            modalidad_imagen_sugerida=modalidad,
            resumen_para_radiologo=resumen,
            disclaimer=DISCLAIMER_CLINICO,
        )

    # ---------------- redaccion (LLM o plantilla) ----------------

    def _redactar_justificacion(self, paciente, entrada, razones) -> str:
        razones_txt = ", ".join(razones[:6])
        if self.llm.mock:
            return (f"Coincidencia con el patron de {entrada['tipo_cancer']} "
                    f"por: {razones_txt}. Biomarcadores tipicos: "
                    f"{', '.join(entrada['biomarcadores'][:3])}.")
        prompt = (
            "Sos un asistente medico que redacta de forma concisa y prudente. "
            "Explica en 2 frases por que el siguiente caso es compatible con el "
            f"diagnostico de {entrada['tipo_cancer']}, mencionando los hallazgos "
            f"coincidentes ({razones_txt}). No afirmes certezas; usa lenguaje de "
            "sospecha clinica.\n\n"
            f"Caso: {paciente.a_texto_clinico()}"
        )
        salida = self.llm.generar(prompt)
        if '"_mock"' in salida or not salida.strip():
            return (f"Coincidencia con el patron de {entrada['tipo_cancer']} por: {razones_txt}.")
        return salida.strip()

    def _redactar_resumen_radiologo(self, paciente, hipotesis_fuertes, requiere_imagen) -> str:
        if not requiere_imagen or not hipotesis_fuertes:
            return ("No se identifica indicacion clara de estudio de imagen oncologico "
                    "con la informacion disponible. Se sugiere seguimiento clinico.")
        principal = hipotesis_fuertes[0]["entrada"]
        base = (
            f"Paciente derivado con sospecha de {principal['tipo_cancer']}. "
            f"Estudio sugerido: {principal['modalidad_imagen_sugerida']}. "
            f"Foco de lectura: {principal['guia_radiologo']}"
        )
        if self.llm.mock:
            return base
        prompt = (
            "Redacta un resumen breve (3-4 frases) para un radiologo, a partir de "
            "esta informacion, indicando la sospecha diagnostica y que debe priorizar "
            "en la lectura. Tono profesional y prudente.\n\n" + base
        )
        salida = self.llm.generar(prompt)
        if '"_mock"' in salida or not salida.strip():
            return base
        return salida.strip()
