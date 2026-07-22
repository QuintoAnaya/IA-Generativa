"""
Base de conocimiento oncologica y recuperacion de hipotesis (RAG).

El retrieval no usa embeddings. Usa coincidencia de terminos clinicos
normalizados, ponderados por especificidad (IDF), mas un conjunto de señales
clinicas que se puntuan por separado. La razon de esta eleccion es la
trazabilidad: cada hipotesis que el sistema propone puede justificarse
enumerando exactamente que evidencia la sostiene (que sintomas, que factores
de riesgo, que biomarcadores), lo que en un dominio medico pesa mas que la
mejora marginal de similaridad semantica que aportaria un embedding.

La recuperacion tampoco consume contexto del LLM: todo el scoring se resuelve
en CPU antes de cualquier llamada al modelo generativo.
"""

from __future__ import annotations

import json
import math
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# Terminos sin valor discriminativo. Se excluyen del scoring para que no
# compitan con los terminos clinicos reales.
STOPWORDS = {
    "el", "la", "los", "las", "un", "una", "unos", "unas", "de", "del", "en",
    "y", "o", "u", "a", "ante", "bajo", "con", "contra", "desde", "durante",
    "entre", "hacia", "hasta", "mediante", "para", "por", "segun", "sin",
    "sobre", "tras", "que", "se", "su", "sus", "al", "lo", "le", "les",
    "es", "son", "fue", "fueron", "ser", "esta", "estan", "hay", "habia",
    "tiene", "tenia", "hace", "hacen", "presenta", "presento",
    "muy", "tan", "mas", "menos", "asi", "ya", "aun", "aunque", "cuando",
    "donde", "como", "porque", "ademas", "tambien", "actual", "actualmente",
    "previo", "previa", "reciente", "paciente", "antecedente", "antecedentes",
    "historia", "evolucion", "semanas", "meses", "dias", "anos", "ano",
    "cuadro", "caso", "clinico", "clinica", "general", "leve", "moderado",
    "sintoma", "sintomas", "asintomatico", "asintomatica", "signos", "alarma",
    # Vocabulario de consulta de rutina: aparece por igual en pacientes sanos
    # y enfermos, de modo que sumarlo al score genera falsos positivos.
    "control", "consulta", "revision", "chequeo", "rutina", "seguimiento",
    "resultado", "resultados", "informe", "estudio", "examen", "normal",
}

# Normalizacion de vocabulario. El dataset mezcla terminologia en espanol
# (historias clinicas) con terminologia en ingles (prompts de imagen, algunos
# nombres de biomarcadores) y alterna registro tecnico y coloquial. Sin esta
# tabla, "kidney" y "rinon" se tratan como terminos distintos y no matchean.
SYNONYMS = {
    "lung": "pulmon", "pulmonary": "pulmon", "pulmonar": "pulmon",
    "kidney": "rinon", "renal": "rinon",
    "liver": "higado", "hepatic": "higado", "hepatico": "higado",
    "stomach": "estomago", "gastric": "estomago", "gastrico": "estomago",
    "thyroid": "tiroides", "tiroideo": "tiroides",
    "adrenal": "suprarrenal",
    "colorectal": "colon", "rectal": "colon", "intestinal": "colon",
    "pancreatic": "pancreas", "pancreatico": "pancreas",
    "biliary": "biliar",
    "lymphoma": "linfoma", "lymph": "ganglio", "adenopatia": "ganglio",
    "tumor": "masa", "nodulo": "masa", "lesion": "masa", "bulto": "masa",
    "cancer": "carcinoma", "neoplasia": "carcinoma",
    "computed": "tomografia", "tomography": "tomografia",
    "sangrado": "hemorragia",
}

# Terminos que anclan un caso a un organo concreto. Se usan como señal de
# especificidad anatomica: dos condiciones pueden compartir vocabulario clinico
# generico ("masa", "dolor", "perdida de peso") y distinguirse unicamente por el
# organo comprometido. Sin esta señal el retrieval confunde de forma sistematica
# entidades de organos vecinos, por ejemplo rinon y suprarrenal.
ORGAN_TERMS = {
    "pulmon": {"pulmon", "torax", "toracico", "tos", "disnea", "hemoptisis",
               "esputo", "respiratorio", "pleural", "bronquio", "hiliar"},
    "rinon": {"rinon", "hematuria", "flanco", "lumbar", "orina", "urinario",
              "bosniak", "nefrologia", "urologia"},
    "higado": {"higado", "ictericia", "biliar", "colangio", "hepatomegalia",
               "cirrosis", "afp", "hipocondrio"},
    "pancreas": {"pancreas", "ictericia", "epigastrio", "esteatorrea", "diabetes"},
    "estomago": {"estomago", "epigastrio", "melena", "saciedad", "dispepsia", "pirosis"},
    "colon": {"colon", "heces", "deposiciones", "rectorragia", "diverticulo",
              "diverticular", "abdominal", "hematoquecia"},
    "intestino": {"colon", "heces", "deposiciones", "abdominal"},
    "tiroides": {"tiroides", "cuello", "cervical", "disfonia", "tsh", "deglucion"},
    "linfoide": {"ganglio", "linfoma", "cervical", "axilar", "supraclavicular",
                 "esplenomegalia", "sudoracion", "nocturna"},
    "suprarrenal": {"suprarrenal", "cortisol", "aldosterona", "metanefrina",
                    "hipertension", "virilizacion", "cushing"},
}


def normalize_text(text) -> str:
    """Minusculas, sin tildes, solo alfanumerico, con sinonimos unificados."""
    text = unicodedata.normalize("NFKD", str(text).lower())
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    return " ".join(SYNONYMS.get(tok, tok) for tok in text.split())


def tokenize(text) -> set:
    return {t for t in normalize_text(text).split() if len(t) > 2 and t not in STOPWORDS}


def flatten(value) -> str:
    if value is None:
        return ""
    if isinstance(value, dict):
        return " ".join(flatten(v) for v in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(flatten(v) for v in value)
    return str(value)


def coverage(query_tokens: set, field_tokens: set, idf_fn) -> float:
    """Fraccion del vocabulario del paciente, ponderada por especificidad, que
    queda explicada por un campo de la entrada.

    Se usa cobertura y no indice de Jaccard porque Jaccard divide por la union
    de ambos vocabularios, lo que penaliza a las entradas con descripciones mas
    extensas aunque compartan mas terminos especificos con el paciente. En una
    base donde el nivel de detalle varia entre entradas, esa penalizacion
    introduce un sesgo sin justificacion clinica.
    """
    if not query_tokens or not field_tokens:
        return 0.0
    shared = query_tokens & field_tokens
    if not shared:
        return 0.0
    return sum(idf_fn(t) for t in shared) / max(1e-9, sum(idf_fn(t) for t in query_tokens))


@dataclass
class GroundTruthEntry:
    raw: dict

    @property
    def gt_id(self) -> str:
        return self.raw["gt_id"]

    @property
    def icd_10(self) -> str:
        return self.raw.get("icd_10", "")

    @property
    def icd_10_description(self) -> str:
        return self.raw.get("icd_10_description", "")

    @property
    def base_probability(self) -> float:
        return float(self.raw.get("base_probability", 0.5))

    @property
    def urgency_level(self) -> str:
        return self.raw.get("urgency_level", "media")

    @property
    def organ(self) -> str:
        return self.raw.get("_meta", {}).get("organ", "")

    @property
    def radiologist_guidance(self) -> dict:
        return self.raw.get("radiologist_guidance", {}) or {}

    @property
    def objective_data(self) -> dict:
        return self.raw.get("objective_data", {}) or {}

    @property
    def subjective_data(self) -> dict:
        return self.raw.get("subjective_data", {}) or {}

    def biomarkers(self) -> dict:
        return self.objective_data.get("biomarkers", {}) or {}

    def field_tokens(self) -> dict:
        """Tokens agrupados por campo clinico. Se mantienen separados, en vez de
        concatenarse en un unico bloque de texto, para poder puntuar cada tipo
        de evidencia por su cuenta y reportar despues cual sostiene la hipotesis.
        """
        return {
            "symptoms": tokenize(
                flatten(self.subjective_data.get("symptoms")) + " "
                + flatten(self.subjective_data.get("patient_reported_concerns"))
            ),
            "findings": tokenize(flatten(self.objective_data.get("clinical_findings"))),
            "risk_factors": tokenize(flatten(self.objective_data.get("risk_factors"))),
            "red_flags": tokenize(flatten(self.objective_data.get("prior_imaging_red_flags"))),
        }

    def all_tokens(self) -> set:
        merged = set()
        for toks in self.field_tokens().values():
            merged |= toks
        return merged | tokenize(self.icd_10_description)


@dataclass
class RetrievalResult:
    """Resultado del retrieval para una entrada, con la evidencia desagregada."""
    gt_id: str
    relevance: float
    signals: dict
    evidence: list = field(default_factory=list)
    matched_biomarkers: list = field(default_factory=list)


class KnowledgeBase:
    def __init__(self, entries: list):
        self.entries = entries
        self._idf = self._compute_idf()
        self._field_cache = {e.gt_id: e.field_tokens() for e in entries}

    @staticmethod
    def load(path: str) -> "KnowledgeBase":
        base_dir = Path(path)
        entries = [
            GroundTruthEntry(raw=json.loads(f.read_text(encoding="utf-8")))
            for f in sorted(base_dir.glob("*.json"))
        ]
        if not entries:
            raise FileNotFoundError(f"No se encontraron entradas de ground truth en {base_dir}.")
        return KnowledgeBase(entries=entries)

    def __len__(self) -> int:
        return len(self.entries)

    def get(self, gt_id: str) -> Optional[GroundTruthEntry]:
        for e in self.entries:
            if e.gt_id == gt_id:
                return e
        return None

    def _compute_idf(self) -> dict:
        """Especificidad de cada termino dentro de la base.

        Un termino presente en casi todas las entradas (por ejemplo "masa" o
        "carcinoma", habituales en cualquier base oncologica) no discrimina entre
        hipotesis y debe pesar poco. Uno que aparece en una o dos entradas
        ("hematuria", "ictericia") es el que efectivamente separa diagnosticos.
        """
        n_docs = len(self.entries)
        doc_freq: dict = {}
        for e in self.entries:
            for t in e.all_tokens():
                doc_freq[t] = doc_freq.get(t, 0) + 1
        return {t: math.log((n_docs + 1) / (df + 1)) + 1.0 for t, df in doc_freq.items()}

    def idf(self, term: str) -> float:
        return self._idf.get(term, math.log(len(self.entries) + 1) + 1.0)

    def score_entry(self, query_tokens: set, labs: dict, age, entry: GroundTruthEntry) -> RetrievalResult:
        fields = self._field_cache[entry.gt_id]

        s_symptoms = coverage(query_tokens, fields["symptoms"], self.idf)
        s_findings = coverage(query_tokens, fields["findings"], self.idf)
        s_risk = coverage(query_tokens, fields["risk_factors"], self.idf)
        s_flags = coverage(query_tokens, fields["red_flags"], self.idf)

        organ_terms = ORGAN_TERMS.get(entry.organ, set())
        organ_hits = query_tokens & organ_terms
        s_organ = min(1.0, len(organ_hits) / 2.0) if organ_terms else 0.0

        matched_biomarkers = []
        biomarkers = entry.biomarkers()
        for name, rule in biomarkers.items():
            patient_value = _lookup_lab(labs, name)
            if patient_value is not None and _threshold_satisfied(patient_value, rule):
                matched_biomarkers.append(f"{name}={patient_value}")
        s_biomarkers = len(matched_biomarkers) / max(1, len(biomarkers)) if biomarkers else 0.0

        # Factor de riesgo etario. Varias entradas expresan la edad como factor
        # de riesgo en texto libre ("edad > 50 anos"); la coincidencia de
        # terminos no lo captura porque el paciente aporta un numero y no la
        # palabra, de modo que se evalua aparte.
        age_evidence = False
        if isinstance(age, (int, float)):
            risk_text = normalize_text(flatten(entry.objective_data.get("risk_factors")))
            threshold_match = re.search(r"edad\s*>\s*(\d+)", risk_text)
            if threshold_match and age >= int(threshold_match.group(1)):
                s_risk = max(s_risk, 0.40)
                age_evidence = True

        # Suficiencia de informacion. Un caso descripto con muy pocos terminos
        # informativos no aporta base para sostener ninguna hipotesis: con un
        # vocabulario de una o dos palabras, un unico termino coincidente
        # produce cobertura total y la relevancia se dispara sin evidencia real.
        # El factor atenua la relevancia de forma proporcional hasta alcanzar un
        # minimo de vocabulario clinico.
        sufficiency = min(1.0, len(query_tokens) / 5.0)

        relevance = sufficiency * (
            0.30 * s_symptoms
            + 0.24 * s_findings
            + 0.14 * s_risk
            + 0.10 * s_flags
            + 0.12 * s_organ
            + 0.10 * s_biomarkers
        )

        # Evidencia legible. Una hipotesis que no puede enumerar sobre que se
        # apoya no se propone (ver `retrieve`): el sistema tiene que poder
        # responder siempre por que sugirio lo que sugirio.
        evidence = []
        if s_symptoms > 0:
            evidence.append("síntomas compatibles")
        if s_findings > 0:
            evidence.append("hallazgos clínicos compatibles")
        if organ_hits:
            evidence.append(f"compromiso de {entry.organ}")
        if age_evidence:
            evidence.append(f"edad ({age} años) dentro del grupo de riesgo")
        elif s_risk > 0:
            evidence.append("factores de riesgo compatibles")
        if s_flags > 0:
            evidence.append("antecedente de imagen con signos de alarma")
        if matched_biomarkers:
            evidence.append("biomarcadores alterados: " + ", ".join(matched_biomarkers))

        return RetrievalResult(
            gt_id=entry.gt_id,
            relevance=relevance,
            signals={
                "symptoms": round(s_symptoms, 4),
                "findings": round(s_findings, 4),
                "risk_factors": round(s_risk, 4),
                "red_flags": round(s_flags, 4),
                "organ_specificity": round(s_organ, 4),
                "biomarkers": round(s_biomarkers, 4),
            },
            evidence=evidence,
            matched_biomarkers=matched_biomarkers,
        )

    def retrieve(self, patient_text: str, labs: dict, age=None,
                 candidate_threshold: float = 0.03, top_k_context: int = 5) -> dict:
        """Puntua la base completa contra el caso y devuelve las candidatas.

        `candidates` son todas las entradas con señal por encima del umbral, es
        decir lo que el RAG recupero. `in_context` son las top-k que
        efectivamente se le pasarian al LLM. La diferencia entre ambas
        cantidades es la compresion de contexto que reporta `token_usage`.
        """
        query_tokens = tokenize(patient_text)
        scored = [self.score_entry(query_tokens, labs, age, e) for e in self.entries]
        scored.sort(key=lambda r: r.relevance, reverse=True)

        candidates = [r for r in scored if r.relevance > candidate_threshold and r.evidence]
        in_context = candidates[:top_k_context]

        return {
            "candidates": candidates,
            "in_context": in_context,
            "retrieved_gt_entries": len(candidates),
            "gt_entries_in_context": len(in_context),
        }


def _lookup_lab(labs: dict, biomarker_name: str):
    """Busca el valor de un biomarcador entre los labs del paciente, tolerando
    diferencias de mayusculas, tildes y separadores en el nombre del campo.
    """
    if not labs:
        return None
    target = normalize_text(biomarker_name).replace(" ", "_")
    for k, v in labs.items():
        if normalize_text(k).replace(" ", "_") == target:
            return v
    return None


def _threshold_satisfied(patient_value, rule) -> bool:
    """Decide si el valor del paciente cumple la condicion de anormalidad que
    describe el ground truth.

    Solo devuelve True cuando la regla expresa un umbral numerico explicito
    ("> 37 U/mL", "< 12 g/dL") y el valor del paciente lo supera. Las
    descripciones puramente cualitativas del dataset ("elevada", "variable",
    "expresion variable") no se cuentan como evidencia: no son verificables
    contra un numero, y aceptarlas hacia que cualquier paciente con un lab
    cargado sumara evidencia a favor de decenas de entradas que comparten
    marcadores inespecificos como LDH o VSG. Es una decision conservadora
    deliberada, documentada como limitacion en el README.
    """
    if isinstance(patient_value, bool) or not isinstance(patient_value, (int, float)):
        return False
    match = re.search(r"([><])\s*=?\s*([\d.,]+)", str(rule))
    if not match:
        return False
    operator, raw_number = match.group(1), match.group(2)
    try:
        # Distingue separador de miles ("12.000") de separador decimal ("1.5").
        if raw_number.count(".") == 1 and len(raw_number.split(".")[1]) == 3:
            threshold = float(raw_number.replace(".", ""))
        else:
            threshold = float(raw_number.replace(",", "."))
    except ValueError:
        return False
    return patient_value > threshold if operator == ">" else patient_value < threshold
