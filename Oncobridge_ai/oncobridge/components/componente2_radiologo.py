"""
Componente 2 - Asistencia Radiologica (asistente del especialista en imagenes).

Recibe:
  - El resumen-puente del Componente 1 (que hipotesis trae el oncologo).
  - El estudio de imagen (EstudioImagenInput): modalidad, region y hallazgos
    estructurados. Opcionalmente, la ruta a una imagen real.

Produce (SalidaComponente2):
  - Guia de lectura: que buscar y donde, segun la base de conocimiento.
  - Correlacion de los hallazgos del estudio con el patron esperado.
  - Concordancia con la hipotesis del oncologo.
  - Un informe orientado (borrador) para que el radiologo edite y valide.

MODO IMAGEN REAL (amplio): si se pasa ruta_imagen y hay soporte disponible,
el componente extrae metadata basica de la imagen (dimensiones, formato) y,
si es un DICOM, lee sus tags. NO pretende diagnosticar sobre los pixeles: la
lectura la hace el radiologo. El sistema orienta, no reemplaza.
"""

import os
from oncobridge.knowledge.knowledge_base import KnowledgeBase
from oncobridge.utils.llm_client import LLMClient
from oncobridge.utils.schemas import (
    EstudioImagenInput, SalidaComponente1, SalidaComponente2, DISCLAIMER_CLINICO
)


class ComponenteRadiologo:
    def __init__(self, kb: KnowledgeBase | None = None, llm: LLMClient | None = None):
        self.kb = kb or KnowledgeBase()
        self.llm = llm or LLMClient()

    def procesar(self, estudio: EstudioImagenInput,
                 contexto_c1: SalidaComponente1 | None = None) -> SalidaComponente2:

        # 1. Determinar el patron esperado. Preferimos la hipotesis del Componente 1;
        #    si no hay, inferimos por region anatomica / modalidad.
        entrada_kb = self._resolver_entrada(estudio, contexto_c1)

        # 2. (Opcional) Inspeccionar la imagen real si se proporciono.
        metadata_imagen = self._inspeccionar_imagen(estudio.ruta_imagen) if estudio.ruta_imagen else {}

        # 3. Correlacionar hallazgos del estudio con el patron esperado.
        hallazgos_correlacionados, concordancia = self._correlacionar(estudio, entrada_kb)

        # 4. Guia de lectura.
        if entrada_kb:
            guia = entrada_kb["guia_radiologo"]
        else:
            guia = ("Sin patron especifico en la base para esta modalidad/region. "
                    "Realizar lectura sistematica estandar del estudio.")

        # 5. Informe orientado (borrador).
        informe = self._redactar_informe(estudio, entrada_kb, hallazgos_correlacionados,
                                          concordancia, metadata_imagen)

        return SalidaComponente2(
            estudio_id=estudio.estudio_id,
            guia_lectura=guia,
            hallazgos_correlacionados=hallazgos_correlacionados,
            concordancia_con_hipotesis=concordancia,
            informe_orientado=informe,
            disclaimer=DISCLAIMER_CLINICO,
        )

    # ---------------- internos ----------------

    def _resolver_entrada(self, estudio, contexto_c1):
        # Prioridad 1: la hipotesis principal del oncologo.
        if contexto_c1 and contexto_c1.hipotesis:
            principal = contexto_c1.hipotesis[0]
            entrada = self.kb.buscar_por_tipo(principal.tipo_cancer)
            if entrada:
                return entrada
        # Prioridad 2: inferir por region anatomica combinando con hallazgos.
        query = f"{estudio.region_anatomica} {estudio.modalidad} " + " ".join(estudio.hallazgos_estructurados)
        recuperadas = self.kb.recuperar(query, top_k=1)
        return recuperadas[0]["entrada"] if recuperadas else None

    def _inspeccionar_imagen(self, ruta: str) -> dict:
        """Extrae metadata de una imagen real si esta disponible. No diagnostica."""
        meta = {"ruta": ruta, "existe": os.path.exists(ruta)}
        if not meta["existe"]:
            meta["nota"] = "El archivo de imagen no existe en la ruta indicada."
            return meta
        ext = os.path.splitext(ruta)[1].lower()
        try:
            if ext in (".dcm", ".dicom"):
                import pydicom
                ds = pydicom.dcmread(ruta, stop_before_pixels=True)
                meta.update({
                    "formato": "DICOM",
                    "modalidad_dicom": getattr(ds, "Modality", "?"),
                    "parte_cuerpo": getattr(ds, "BodyPartExamined", "?"),
                    "dimensiones": f"{getattr(ds, 'Rows', '?')}x{getattr(ds, 'Columns', '?')}",
                })
            else:
                from PIL import Image
                with Image.open(ruta) as img:
                    meta.update({"formato": img.format, "dimensiones": f"{img.width}x{img.height}"})
        except ImportError as e:
            meta["nota"] = f"Libreria para leer la imagen no instalada ({e}). Se omite metadata."
        except Exception as e:
            meta["nota"] = f"No se pudo leer la imagen: {e}"
        return meta

    def _correlacionar(self, estudio, entrada_kb):
        """Compara hallazgos del estudio con el patron esperado de la base."""
        if not entrada_kb:
            return list(estudio.hallazgos_estructurados), "Sin patron de referencia para correlacionar."

        patron = (entrada_kb.get("patron_imagen_esperado", "") + " " +
                  entrada_kb.get("guia_radiologo", "")).lower()

        correlacionados = []
        n_match = 0
        for h in estudio.hallazgos_estructurados:
            # un hallazgo "correlaciona" si alguna de sus palabras clave aparece en el patron
            palabras = [p for p in h.lower().split() if len(p) > 4]
            if any(p in patron for p in palabras):
                correlacionados.append(f"[COMPATIBLE] {h}")
                n_match += 1
            else:
                correlacionados.append(f"[a evaluar] {h}")

        total = len(estudio.hallazgos_estructurados) or 1
        ratio = n_match / total
        if ratio >= 0.6:
            concordancia = (f"ALTA concordancia con el patron de {entrada_kb['tipo_cancer']} "
                            f"({n_match}/{total} hallazgos compatibles).")
        elif ratio > 0:
            concordancia = (f"Concordancia PARCIAL con {entrada_kb['tipo_cancer']} "
                            f"({n_match}/{total} hallazgos compatibles). Considerar diferenciales: "
                            f"{', '.join(entrada_kb.get('diferenciales', [])[:3])}.")
        else:
            concordancia = (f"BAJA concordancia con {entrada_kb['tipo_cancer']}. "
                            f"Revisar diferenciales: {', '.join(entrada_kb.get('diferenciales', [])[:3])}.")
        return correlacionados, concordancia

    def _redactar_informe(self, estudio, entrada_kb, correlacionados, concordancia, metadata_imagen):
        tipo = entrada_kb["tipo_cancer"] if entrada_kb else "hallazgo inespecifico"
        lineas = [
            f"INFORME ORIENTADO (BORRADOR - requiere validacion del radiologo)",
            f"Estudio: {estudio.modalidad} de {estudio.region_anatomica} (ID {estudio.estudio_id}).",
            f"Sospecha orientadora: {tipo}.",
        ]
        if metadata_imagen and metadata_imagen.get("existe"):
            lineas.append(f"Imagen: {metadata_imagen.get('formato','?')}, "
                          f"{metadata_imagen.get('dimensiones','?')}.")
        lineas.append("Hallazgos evaluados: " + "; ".join(correlacionados) + ".")
        lineas.append(concordancia)
        base = "\n".join(lineas)

        if self.llm.mock:
            return base
        prompt = (
            "Redacta un borrador de informe radiologico breve y estructurado a partir "
            "de estos datos. Marca claramente que es un borrador que el radiologo debe "
            "validar. No inventes hallazgos que no esten listados.\n\n" + base
        )
        salida = self.llm.generar(prompt)
        if '"_mock"' in salida or not salida.strip():
            return base
        return salida.strip()
