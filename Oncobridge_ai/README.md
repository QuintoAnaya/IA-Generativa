# OncoBridge AI — Sistema de Apoyo al Diagnóstico Oncológico

**Trabajo Final — IA Generativa para Biomedicina | Universidad Austral**

OncoBridge AI es un sistema de apoyo a la decisión clínica (CDSS) que hace consultable, en tiempo real, una base de conocimiento oncológica curada. Dado el contexto clínico de un paciente, el sistema identifica las hipótesis diagnósticas más probables, decide si corresponde derivar a un estudio de imagen y con qué urgencia, y le entrega al radiólogo una guía de lectura orientada al caso.

> **OncoBridge AI asiste — no reemplaza.** La decisión diagnóstica y terapéutica final es siempre del médico.

---

## Objetivos

- Cerrar la brecha entre el conocimiento oncológico acumulado y su uso en el punto de decisión clínica.
- Reducir la variabilidad en la derivación a estudios de imagen.
- Entregarle al especialista en imágenes el contexto clínico y la guía de lectura que hoy se pierde entre la consulta y la lectura del estudio.

---

## Arquitectura del sistema

El sistema se compone de dos componentes que colaboran de forma secuencial, sobre una base de conocimiento común.

```
                       ┌─────────────────────────────────┐
                       │   BASE DE CONOCIMIENTO ONCOLÓGICA │
                       │   (15 patrones diagnósticos,      │
                       │    biomarcadores, guías de imagen) │
                       └───────────────┬─────────────────┘
                                       │ retrieval (recuperación)
                                       │
   PacienteInput                       ▼
   (edad, síntomas,      ┌──────────────────────────────┐
    factores de riesgo,  │   COMPONENTE 1 — ONCÓLOGO     │
    biomarcadores)  ───► │  • recupera hipótesis          │
                         │  • decide si requiere imagen   │
                         │  • asigna urgencia de triage   │
                         │  • redacta resumen-puente      │
                         └───────────────┬──────────────┘
                                         │ SalidaComponente1
                                         │ (hipótesis + resumen para el radiólogo)
                                         ▼
   EstudioImagenInput    ┌──────────────────────────────┐
   (modalidad, región,   │   COMPONENTE 2 — RADIÓLOGO    │
    hallazgos, imagen    │  • guía de lectura (qué/dónde) │
    real opcional)  ───► │  • correlaciona hallazgos      │
                         │  • evalúa concordancia         │
                         │  • redacta informe orientado   │
                         └───────────────┬──────────────┘
                                         │ SalidaComponente2
                                         ▼
                              Informe orientado (borrador
                              que el radiólogo valida)
```

**Decisión de diseño central:** la lógica clínica (qué hipótesis, si requiere imagen, qué urgencia) proviene del *retrieval* sobre la base de conocimiento curada, **no** del modelo generativo. El LLM (Gemini) se usa solo para **redactar** justificaciones e informes en lenguaje natural. Esto reduce el riesgo de alucinaciones en las decisiones que importan y hace el sistema explicable: cada hipótesis es trazable a una entrada de la base (`kb_id`).

Si no hay API key de Gemini configurada, el sistema funciona igual en **modo simulado**: la lógica clínica sigue intacta (viene de la base), y la redacción usa plantillas. Así el proyecto **siempre corre end-to-end**.

### Estructura del repositorio

```
oncobridge-ai/
├── oncobridge/
│   ├── knowledge/
│   │   └── knowledge_base.py       # carga y retrieval de la base de conocimiento
│   ├── components/
│   │   ├── componente1_oncologo.py # Componente 1
│   │   └── componente2_radiologo.py# Componente 2 (incluye modo imagen real)
│   ├── evaluation/
│   │   └── evaluar.py              # motor de métricas
│   ├── utils/
│   │   ├── schemas.py             # contrato de inputs/outputs (dataclasses)
│   │   └── llm_client.py          # cliente Gemini + fallback a modo simulado
│   └── pipeline.py                # orquestador end-to-end
├── data/
│   ├── knowledge_base/
│   │   └── oncology_kb.json        # base de conocimiento (15 tipos de cáncer)
│   └── eval_dataset/
│       └── casos_evaluacion.json   # 18 casos con ground truth
├── scripts/
│   ├── run_componente1.py
│   ├── run_componente2.py
│   ├── run_pipeline.py
│   └── run_evaluacion.py
├── .env.example                    # plantilla para la API key
├── .gitignore                      # bloquea .env (la key nunca se sube)
├── requirements.txt
├── setup.py
└── README.md
```

---

## Guía de ejecución

Cualquier persona con Python 3.10+ puede correr el sistema desde cero siguiendo estos pasos.

### 1. Instalación de dependencias

```bash
pip install -r requirements.txt
```

> El sistema corre incluso sin dependencias externas en modo simulado, pero se recomienda instalarlas para usar Gemini.

### 2. Configuración de variables de entorno (API key)

```bash
cp .env.example .env
```

Abrí el archivo `.env` y pegá tu API key de Gemini reemplazando `pega_tu_api_key_aca`:

```
GEMINI_API_KEY=tu_api_key_real_aca
```

**Tu key nunca se sube a GitHub:** el archivo `.env` está bloqueado por `.gitignore`. El `.env.example` no contiene ninguna key real.

Si no configurás la key, el sistema corre en **modo simulado** automáticamente.

### 3. Correr el Componente 1 (oncólogo)

```bash
python scripts/run_componente1.py
```

Salida esperada: un JSON con las hipótesis diagnósticas, la decisión de derivación a imagen, la urgencia de triage y el resumen-puente para el radiólogo. Para el caso negativo:

```bash
python scripts/run_componente1.py --ejemplo neg
```

### 4. Correr el Componente 2 (radiólogo)

```bash
python scripts/run_componente2.py
```

Salida esperada: guía de lectura, hallazgos correlacionados, concordancia con la hipótesis e informe orientado (borrador).

Modo imagen real (opcional):

```bash
python scripts/run_componente2.py --imagen /ruta/a/tu/estudio.dcm
```

### 5. Correr el flujo end-to-end

```bash
python scripts/run_pipeline.py            # caso positivo (encadena C1 -> C2)
python scripts/run_pipeline.py --ejemplo neg   # caso negativo (se detiene en C1)
```

### 6. Correr el script de evaluación

```bash
python scripts/run_evaluacion.py
```

Corre los 18 casos del dataset y reporta las métricas. Para guardar los resultados:

```bash
python scripts/run_evaluacion.py --guardar resultados_eval.json
```

---

## Dataset de evaluación y resultados

El dataset (`data/eval_dataset/casos_evaluacion.json`) contiene **18 casos clínicos sintéticos** con *ground truth*: **13 positivos** (cubren distintos tipos de cáncer y deberían derivarse a imagen) y **5 negativos** (cuadros benignos que no requieren estudio oncológico).

Métricas obtenidas (modo simulado):

| Métrica | Valor |
|---|---|
| Derivación a imagen — Precisión | 1.000 |
| Derivación a imagen — Recall | 1.000 |
| Derivación a imagen — F1 | 1.000 |
| Derivación a imagen — Accuracy | 1.000 |
| Diagnóstico top-1 (positivos) | 13/13 = 1.000 |
| Urgencia / triage (positivos) | 11/13 = 0.846 |

La matriz de confusión de la decisión de imagen es TP=13, FP=0, TN=5, FN=0.

> **Nota honesta sobre las métricas:** son altas en parte porque el dataset es sintético y está alineado con la terminología de la base de conocimiento. En datos clínicos reales, con lenguaje libre y ruidoso, el rendimiento sería menor. El valor del ejercicio está en el diseño del flujo y la evaluación, no en tomar estos números como desempeño clínico real.

---

## Limitaciones conocidas y trabajo futuro

- **Retrieval por coincidencia de términos:** es explicable y robusto, pero no capta sinónimos ni paráfrasis. La urgencia falla en 2/13 casos porque se toma de la hipótesis principal y no pondera el resto. *Futuro:* embeddings semánticos para el retrieval y un modelo de urgencia que integre varias señales.
- **Base de conocimiento acotada:** 15 tipos de cáncer. *Futuro:* ampliarla y versionarla con revisión de especialistas.
- **Componente 2 sobre hallazgos estructurados:** el sistema orienta la lectura pero no analiza los píxeles de la imagen. Puede leer metadata de DICOM/PNG/JPG, pero no segmenta ni detecta lesiones. *Futuro:* integrar modelos de visión para segmentación asistida.
- **Datos sintéticos:** no reemplazan validación con datos clínicos reales y aprobación regulatoria.
- **Calibración de confianza:** las probabilidades son confianza relativa del retrieval, no certeza clínica calibrada.

---

## Consideraciones éticas

- El sistema es una **herramienta de apoyo (CDSS)**, no un sustituto del juicio médico.
- **Privacidad:** los datos de pacientes deben anonimizarse y procesarse bajo marcos vigentes (HIPAA / GDPR / Ley 26.529). Este proyecto usa únicamente datos sintéticos.
- **Riesgos:** alucinaciones del LLM (mitigadas al no delegarle la lógica clínica), sesgo del dataset, y calibración de confianza.

---

*Proyecto académico. La base de conocimiento y los casos son sintéticos y no deben usarse para decisiones clínicas reales.*
