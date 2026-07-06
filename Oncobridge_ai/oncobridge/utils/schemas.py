"""
Contrato del sistema: define los inputs y outputs de OncoBridge AI usando dataclasses.

Esto formaliza la seccion 4 del enunciado ("Contrato del Sistema - Inputs y Outputs").
Tener el contrato tipado hace el sistema predecible y facil de evaluar.
"""

from dataclasses import dataclass, field, asdict
from typing import Optional


# ----------------------------- INPUTS -----------------------------

@dataclass
class PacienteInput:
    """Input del Componente 1: contexto clinico del paciente."""
    paciente_id: str
    edad: int
    sexo: str  # "M" / "F"
    motivo_consulta: str
    historia_clinica: str          # texto libre con antecedentes
    sintomas_actuales: list[str] = field(default_factory=list)
    factores_riesgo: list[str] = field(default_factory=list)
    biomarcadores: dict = field(default_factory=dict)  # ej {"PSA": 8.5}

    def a_texto_clinico(self) -> str:
        """Aplana el input a un texto unico para el retrieval y el prompt."""
        partes = [
            f"Paciente {self.sexo}, {self.edad} anos.",
            f"Motivo de consulta: {self.motivo_consulta}.",
            f"Historia clinica: {self.historia_clinica}.",
        ]
        if self.sintomas_actuales:
            partes.append("Sintomas actuales: " + ", ".join(self.sintomas_actuales) + ".")
        if self.factores_riesgo:
            partes.append("Factores de riesgo: " + ", ".join(self.factores_riesgo) + ".")
        if self.biomarcadores:
            bm = ", ".join(f"{k}={v}" for k, v in self.biomarcadores.items())
            partes.append("Biomarcadores: " + bm + ".")
        return " ".join(partes)


@dataclass
class EstudioImagenInput:
    """Input del Componente 2: estudio de imagen + hallazgos estructurados."""
    estudio_id: str
    modalidad: str                 # ej "TC de torax"
    region_anatomica: str          # ej "torax"
    hallazgos_estructurados: list[str] = field(default_factory=list)
    # Opcional: ruta a una imagen real, para el modo "imagen real" del Componente 2.
    ruta_imagen: Optional[str] = None


# ----------------------------- OUTPUTS -----------------------------

@dataclass
class HipotesisDiagnostica:
    """Una hipotesis diagnostica priorizada."""
    tipo_cancer: str
    probabilidad: float            # 0.0 - 1.0 (confianza relativa, NO certeza clinica)
    justificacion: str
    kb_id: str                     # trazabilidad a la entrada de la base


@dataclass
class SalidaComponente1:
    """Output del Componente 1 (consulta oncologica inicial)."""
    paciente_id: str
    requiere_imagen: bool
    urgencia_triage: str           # "alta" / "media" / "baja"
    hipotesis: list[HipotesisDiagnostica] = field(default_factory=list)
    modalidad_imagen_sugerida: str = ""
    resumen_para_radiologo: str = ""   # el "puente" al Componente 2
    disclaimer: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class SalidaComponente2:
    """Output del Componente 2 (asistencia radiologica)."""
    estudio_id: str
    guia_lectura: str              # que buscar y donde
    hallazgos_correlacionados: list[str] = field(default_factory=list)
    concordancia_con_hipotesis: str = ""
    informe_orientado: str = ""
    disclaimer: str = ""

    def to_dict(self):
        return asdict(self)


# ----------------------------- DISCLAIMER GLOBAL -----------------------------

DISCLAIMER_CLINICO = (
    "OncoBridge AI es un sistema de APOYO a la decision clinica (CDSS). "
    "No reemplaza el juicio del medico. La decision diagnostica y terapeutica "
    "final es siempre del especialista. Las probabilidades expresan confianza "
    "relativa del sistema, no certeza clinica."
)
