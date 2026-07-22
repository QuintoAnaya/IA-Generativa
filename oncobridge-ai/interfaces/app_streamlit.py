"""
Interfaz de usuario del prototipo. Presenta los dos componentes con el
vocabulario de cada perfil profesional y sin exponer estructuras JSON.

Ejecucion:
    streamlit run interfaces/app_streamlit.py
"""

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from oncobridge.pipeline import OncoBridgePipeline

st.set_page_config(page_title="OncoBridge AI", layout="wide")

URGENCY_COLOR = {"alta": "#a4342b", "media": "#8a6116", "baja": "#3d6b45", "ninguna": "#54606b"}
RECOMMENDATION_LABEL = {
    "DERIVAR_A_IMAGEN": "Derivar a diagnostico por imagenes",
    "NO_DERIVAR": "No requiere diagnostico por imagenes",
    "SEGUIMIENTO_CLINICO": "Seguimiento clinico",
    "SIN_ELEMENTOS_PARA_EVALUAR": "Datos insuficientes para sostener una hipotesis",
}


@st.cache_resource
def get_pipeline():
    return OncoBridgePipeline(kb_path="data/knowledge_base")


st.title("OncoBridge AI")
st.caption(
    "Sistema de apoyo a la decision oncologica. Los resultados son orientativos y estan "
    "sujetos a revision profesional; el sistema no emite diagnosticos."
)

perfil = st.sidebar.radio("Perfil", ["Componente 1 - Oncologo", "Componente 2 - Radiologo"])

# ---------------------------------------------------------------------------
# Componente 1
# ---------------------------------------------------------------------------
if perfil.startswith("Componente 1"):
    st.subheader("Analisis clinico")

    col_a, col_b = st.columns(2)
    with col_a:
        patient_id = st.text_input("Identificador interno del paciente", value="PAT-00001")
        age = st.number_input("Edad", min_value=0, max_value=120, value=63)
        sex = st.selectbox("Sexo", ["F", "M"])
    with col_b:
        family_history = st.text_area("Antecedentes familiares (uno por linea)",
                                      value="carcinoma_renal\nhipertension", height=90)
        labs_raw = st.text_area("Laboratorio actual (formato 'nombre: valor')",
                                value="hemoglobina: 10.8\nLDH: 320\ncreatinina: 1.3", height=90)

    symptoms_raw = st.text_area(
        "Sintomas actuales (uno por linea)",
        value="hematuria macroscopica intermitente 3 semanas\ndolor lumbar izquierdo persistente\nmasa palpable en flanco izquierdo",
        height=100,
    )
    history_raw = st.text_area(
        "Antecedentes personales (formato 'AAAA-MM: evento')",
        value="2015-04: Hipertension arterial en tratamiento.\n2021-03: Tabaquismo 30 paquetes-ano.",
        height=80,
    )

    anonimizado = st.checkbox(
        "Confirmo que los datos ingresados no contienen informacion identificable del paciente",
        value=False,
    )

    if st.button("Analizar caso", type="primary", disabled=not anonimizado):
        labs = {}
        for line in labs_raw.splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                v = v.strip()
                try:
                    v = float(v)
                except ValueError:
                    pass
                labs[k.strip()] = v

        history = []
        for line in history_raw.splitlines():
            if ":" in line:
                date, event = line.split(":", 1)
                history.append({"date": date.strip(), "event": event.strip()})

        patient = {
            "patient_id": patient_id,
            "demographics": {
                "age": age, "sex": sex,
                "family_history": [f.strip() for f in family_history.splitlines() if f.strip()],
            },
            "current_symptoms": [s.strip() for s in symptoms_raw.splitlines() if s.strip()],
            "medical_history": history,
            "current_labs": labs,
        }

        with st.spinner("Consultando la base de conocimiento"):
            st.session_state["c1"] = get_pipeline().run_component1(patient)

    if not anonimizado:
        st.info("Marque la confirmacion de anonimizacion para habilitar el analisis.")

    if "c1" in st.session_state:
        out = st.session_state["c1"]
        st.divider()

        c1, c2, c3 = st.columns(3)
        c1.metric("Recomendacion", RECOMMENDATION_LABEL.get(out["recommendation"], out["recommendation"]))
        c2.markdown(
            f"**Urgencia**<br><span style='color:{URGENCY_COLOR.get(out['urgency'], '#54606b')};"
            f"font-size:1.4rem;font-weight:600'>{out['urgency'].upper()}</span>",
            unsafe_allow_html=True,
        )
        c3.metric("Probabilidad de requerir imagenes", f"{out['imaging_needed_probability'] * 100:.0f}%")

        st.write(out["clinical_summary"])
        st.write(out["reasoning"])

        if out["matched_ground_truths"]:
            st.markdown("#### Hipotesis recuperadas")
            for m in out["matched_ground_truths"]:
                with st.expander(
                    f"{m['icd_10_description']} ({m['icd_10']}) - coincidencia {m['match_probability'] * 100:.0f}%"
                ):
                    st.write("**Evidencia que la sostiene:** " + m["match_rationale"])
                    st.write("**Modalidades sugeridas:** " + ", ".join(m["radiologist_instructions"]["suggested_modalities"]))
                    st.caption(f"Entrada de la base: {m['gt_id']}")
        else:
            st.warning(
                "No se recupero ninguna hipotesis con evidencia suficiente. Corresponde evaluacion "
                "clinica si los sintomas persisten."
            )

        with st.expander("Trazabilidad tecnica"):
            usage = out["token_usage"]
            st.write(f"Entradas recuperadas por el buscador: {usage['retrieved_gt_entries']}")
            st.write(f"Entradas efectivamente enviadas al modelo de lenguaje: {usage['gt_entries_in_context']}")
            st.write(f"Tokens consumidos: {usage['total_tokens']} (modelo: {usage['model']})")

# ---------------------------------------------------------------------------
# Componente 2
# ---------------------------------------------------------------------------
else:
    st.subheader("Guia de lectura del estudio")

    if "c1" not in st.session_state:
        st.warning("Ejecute primero un analisis en el Componente 1.")
    else:
        c1_out = st.session_state["c1"]
        if not c1_out["matched_ground_truths"]:
            st.warning("El Componente 1 no sostuvo ninguna hipotesis; no hay guia de lectura que generar.")
        else:
            top = c1_out["matched_ground_truths"][0]
            st.write(
                f"Paciente **{c1_out['patient_id']}**. Hipotesis a descartar: "
                f"**{top['icd_10_description']}** ({top['icd_10']})."
            )

            device = st.selectbox(
                "Dispositivo para generar la referencia visual",
                ["auto", "cuda", "cpu"],
                help="Con 'auto' se usa GPU si esta disponible. Sin GPU la generacion es lenta.",
            )

            if st.button("Generar guia de lectura", type="primary"):
                with st.spinner("Generando referencia visual"):
                    st.session_state["c2"] = get_pipeline().run_component2(c1_out, device=device)

            if "c2" in st.session_state:
                out = st.session_state["c2"]
                st.divider()

                # La guia de lectura (modalidades, zonas, notas) proviene de las
                # instrucciones para el radiologo que ya emitio el Componente 1.
                guide = top["radiologist_instructions"]
                location = guide["imaging_location"]

                col_img, col_guide = st.columns([1, 1.3])
                with col_img:
                    ref = out["generated_radiology_reference"]
                    if ref["image_path"] and Path(ref["image_path"]).exists():
                        st.image(ref["image_path"], caption="Referencia sintetica del patron esperado")
                    st.caption(ref["limitation"])

                with col_guide:
                    st.markdown("**Hallazgos esperados / observados**")
                    st.write(out["findings"])

                    st.markdown("**Clasificacion**")
                    st.write(out["classification"].replace("_", " "))

                    st.markdown("**Modalidad sugerida**")
                    st.write(", ".join(guide["suggested_modalities"]) or "no especificada")

                    if guide.get("views_recommended"):
                        st.markdown("**Proyecciones recomendadas**")
                        for v in guide["views_recommended"]:
                            st.write(f"- {v}")

                    st.markdown("**Zonas prioritarias**")
                    for zone in location["priority_zones"]:
                        st.write(f"- {zone}")

                    if location.get("positioning_notes"):
                        st.markdown("**Notas de adquisicion**")
                        st.write(location["positioning_notes"])

                # Region de interes del contrato (segmentation)
                rois = out["segmentation"]["regions_of_interest"]
                if rois:
                    st.markdown("#### Region de interes")
                    for roi in rois:
                        size = roi["size_mm"]
                        size_txt = f"{size} mm" if size is not None else "sin medicion sobre imagen"
                        fuente = "referencia de la base" if roi.get("measurement_source") == "referencia_ground_truth" else "imagen del paciente"
                        st.write(
                            f"- **{roi['location']}** — tamaño: {size_txt} ({fuente}); "
                            f"forma: {roi['shape'].replace('_', ' ')}; "
                            f"margenes: {roi['margins'].replace('_', ' ')}; "
                            f"densidad: {roi['density'].replace('_', ' ')}"
                        )

                st.markdown("#### Indicacion")
                st.write(out["final_recommendation"])
                st.markdown("#### Pasos siguientes")
                for step in out["next_steps"]:
                    st.write(f"- {step.replace('_', ' ')}")
