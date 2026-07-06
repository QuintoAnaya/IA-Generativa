"""
Modulo de acceso a la base de conocimiento oncologica de OncoBridge.

Carga la base curada (JSON) y ofrece metodos de recuperacion (retrieval)
para que los componentes del sistema consulten el conocimiento relevante
segun el contexto clinico de un paciente.

El retrieval es simple y transparente a proposito: usa coincidencia de
terminos clinicos (sintomas, factores de riesgo, biomarcadores) para
puntuar cada entrada de la base. Esto lo hace explicable y reproducible,
lo cual es deseable en un contexto medico.
"""

import json
import unicodedata
from pathlib import Path


# Palabras demasiado genericas: aparecen en casi cualquier caso y no aportan
# senal diagnostica. Se excluyen del indice y de las queries para evitar
# falsos positivos (ej: "dolor", "sintomas" matcheando con todo).
_STOPWORDS_CLINICAS = {
    "dolor", "sintomas", "sintoma", "por", "con", "sin", "para", "una", "uno",
    "del", "los", "las", "que", "the", "and", "reciente", "leve", "ocasional",
    "cambio", "cambios", "aparicion", "generalmente", "muchas", "veces",
    "posible", "posibles", "paciente", "anos", "ano",
}


def _normalizar(texto: str) -> str:
    """Pasa a minusculas y saca tildes para comparar terminos de forma robusta."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return texto


class KnowledgeBase:
    """Base de conocimiento oncologica consultable."""

    def __init__(self, ruta_json: str | Path | None = None):
        if ruta_json is None:
            # ruta por defecto: data/knowledge_base/oncology_kb.json relativa a la raiz del repo
            ruta_json = Path(__file__).resolve().parents[2] / "data" / "knowledge_base" / "oncology_kb.json"
        self.ruta_json = Path(ruta_json)
        with open(self.ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        self.meta = data.get("meta", {})
        self.entradas = data["entradas"]
        # indice normalizado por entrada para acelerar la busqueda
        self._indices = [self._construir_indice(e) for e in self.entradas]

    def _construir_indice(self, entrada: dict) -> set:
        """Junta todos los terminos clinicos de una entrada en un set normalizado."""
        campos = []
        campos += entrada.get("presentacion_clinica", [])
        campos += entrada.get("factores_riesgo", [])
        campos += entrada.get("biomarcadores", [])
        campos.append(entrada.get("tipo_cancer", ""))
        terminos = set()
        for campo in campos:
            for palabra in _normalizar(campo).split():
                if len(palabra) > 2 and palabra not in _STOPWORDS_CLINICAS:
                    terminos.add(palabra)
        return terminos

    def recuperar(self, contexto_clinico: str, top_k: int = 3) -> list[dict]:
        """
        Dado un texto libre con el contexto clinico del paciente, devuelve las
        top_k entradas de la base mas relevantes, cada una con un score de
        coincidencia y las razones (terminos que matchearon).
        """
        terminos_query = set()
        for palabra in _normalizar(contexto_clinico).split():
            if len(palabra) > 2 and palabra not in _STOPWORDS_CLINICAS:
                terminos_query.add(palabra)

        resultados = []
        for entrada, indice in zip(self.entradas, self._indices):
            coincidencias = terminos_query & indice
            score = len(coincidencias)
            if score > 0:
                resultados.append({
                    "entrada": entrada,
                    "score": score,
                    "razones": sorted(coincidencias),
                })

        resultados.sort(key=lambda r: r["score"], reverse=True)
        return resultados[:top_k]

    def buscar_por_tipo(self, tipo_cancer: str) -> dict | None:
        """Devuelve la entrada cuyo tipo de cancer coincide (parcial, normalizado)."""
        objetivo = _normalizar(tipo_cancer)
        for entrada in self.entradas:
            if objetivo in _normalizar(entrada["tipo_cancer"]):
                return entrada
        return None

    def __len__(self):
        return len(self.entradas)
