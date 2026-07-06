"""
Orquestador end-to-end de OncoBridge AI.

Encadena el Componente 1 (oncologo) con el Componente 2 (radiologo):
  PacienteInput  ->  [Componente 1]  ->  SalidaComponente1 (incluye resumen-puente)
                                            |
                     EstudioImagenInput  ->  [Componente 2]  ->  SalidaComponente2

Si el Componente 1 determina que NO se requiere imagen, el flujo se detiene ahi
(no se llama al radiologo), que es el comportamiento clinico correcto.
"""

from dataclasses import dataclass
from oncobridge.knowledge.knowledge_base import KnowledgeBase
from oncobridge.utils.llm_client import LLMClient
from oncobridge.utils.schemas import PacienteInput, EstudioImagenInput, SalidaComponente1, SalidaComponente2
from oncobridge.components.componente1_oncologo import ComponenteOncologo
from oncobridge.components.componente2_radiologo import ComponenteRadiologo


@dataclass
class ResultadoPipeline:
    salida_c1: SalidaComponente1
    salida_c2: SalidaComponente2 | None  # None si no se requirio imagen
    modo_llm: str


class OncoBridgePipeline:
    def __init__(self, forzar_mock: bool = False):
        self.kb = KnowledgeBase()
        self.llm = LLMClient(forzar_mock=forzar_mock)
        self.c1 = ComponenteOncologo(kb=self.kb, llm=self.llm)
        self.c2 = ComponenteRadiologo(kb=self.kb, llm=self.llm)

    def run(self, paciente: PacienteInput,
            estudio: EstudioImagenInput | None = None) -> ResultadoPipeline:
        salida_c1 = self.c1.procesar(paciente)

        salida_c2 = None
        if salida_c1.requiere_imagen:
            # Si no nos pasaron un estudio concreto, generamos uno "placeholder"
            # a partir de la modalidad sugerida, para poder demostrar el flujo.
            if estudio is None:
                estudio = EstudioImagenInput(
                    estudio_id=f"AUTO-{paciente.paciente_id}",
                    modalidad=salida_c1.modalidad_imagen_sugerida or "estudio de imagen",
                    region_anatomica="(segun sospecha)",
                    hallazgos_estructurados=[],
                )
            salida_c2 = self.c2.procesar(estudio, contexto_c1=salida_c1)

        return ResultadoPipeline(salida_c1=salida_c1, salida_c2=salida_c2, modo_llm=self.llm.modo)
