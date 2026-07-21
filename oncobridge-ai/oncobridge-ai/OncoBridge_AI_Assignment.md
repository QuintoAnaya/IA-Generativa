# OncoBridge AI
## Trabajo Final — IA Generativa para Biomedicina
**Universidad Austral | Abril 2026**

---

| | |
|---|---|
| **Proyecto** | OncoBridge AI — Sistema de Apoyo al Diagnóstico Oncológico |
| **Materia** | IA Generativa para Biomedicina |
| **Entrega** | Presentación en Loom + Repositorio GitHub |
| **Fecha** | Abril 2026 |

---

## Tabla de Contenidos

1. [Visión General del Proyecto](#1-visión-general-del-proyecto)
2. [Descripción del Problema Resuelto](#2-descripción-del-problema-resuelto)
3. [Por Qué Tiene Valor lo Aprendido](#3-por-qué-tiene-valor-lo-aprendido)
4. [Contrato del Sistema — Inputs y Outputs](#4-contrato-del-sistema--inputs-y-outputs)
5. [Dataset de Tests y Evaluación](#5-dataset-de-tests-y-evaluación)
6. [Repositorio GitHub](#6-repositorio-github)
7. [Presentación en Loom — Estructura Requerida](#7-presentación-en-loom--estructura-requerida)
8. [Criterios de Evaluación](#8-criterios-de-evaluación)
9. [Consideraciones Éticas y Limitaciones](#9-consideraciones-éticas-y-limitaciones)

---

## 1. Visión General del Proyecto

OncoBridge es una empresa de salud digital cuya misión es cerrar la brecha entre el conocimiento oncológico acumulado y la capacidad real de los especialistas de utilizarlo en el momento de la consulta. A lo largo de años de trabajo con instituciones de salud, OncoBridge construyó una **base de datos oncológica curada de escala industrial** — miles de entradas clínicas estructuradas que describen patrones diagnósticos, biomarcadores, presentaciones clínicas y guías de imagen para los principales tipos de cáncer y sus diferenciales. Esta base representa una ventaja competitiva única en la industria.

El problema es que **ese conocimiento está atrapado en una base de datos que los médicos no pueden consultar eficientemente en el flujo real de una consulta**. Un oncólogo no puede revisar miles de entradas mientras un paciente espera. Un radiólogo no puede buscar manualmente el patrón de imagen correcto para cada hipótesis diagnóstica antes de abrir un estudio. La base existe, es valiosa, y sin embargo no llega al punto de decisión clínica donde más impacta.

OncoBridge AI es el sistema que resuelve ese problema: una interfaz de IA Generativa que, dado el contexto clínico de un paciente, consulta automáticamente la base de conocimiento, identifica las hipótesis diagnósticas más probables y entrega al oncólogo y al radiólogo la información correcta, en el momento correcto, en el formato que pueden usar.

El sistema integra dos componentes que colaboran de manera secuencial: uno orientado al análisis del historial clínico del paciente, y otro orientado a asistir al especialista en imágenes durante la lectura del estudio — indicándole qué buscar y dónde, sin reemplazar su criterio ni su análisis.

> **Misión del sistema:** Hacer que el conocimiento oncológico acumulado por OncoBridge sea accesible y accionable en tiempo real para cada especialista, en cada consulta, reduciendo la variabilidad diagnóstica y acelerando el triage sin agregar carga cognitiva al médico. **OncoBridge AI asiste — no reemplaza. La decisión diagnóstica y terapéutica final es siempre del médico.**

La arquitectura concreta del sistema, las tecnologías utilizadas y las decisiones de diseño son responsabilidad de cada equipo. Lo que este documento especifica es el problema a resolver, el comportamiento esperado del sistema (contrato de inputs/outputs) y cómo se va a evaluar.

---

## 2. Descripción del Problema Resuelto

La oncología enfrenta un desafío estructural de eficiencia: el volumen creciente de pacientes supera la capacidad de atención personalizada de los especialistas. Este cuello de botella se manifiesta en dos etapas críticas del flujo diagnóstico.

### 2.1 Componente 1 — Consulta Oncológica Inicial

El oncólogo debe revisar manualmente el historial clínico completo de cada paciente para contextualizar los síntomas actuales. Los principales problemas identificados son:

- Voluminoso historial clínico que requiere síntesis manual antes de cada consulta.
- Falta de estandarización en la evaluación del riesgo de requerir estudios de imagen.
- Decisiones de derivación basadas en criterios subjetivos y experiencia individual.
- Alta variabilidad inter-médico en el umbral de derivación a estudios costosos.
- La base de conocimiento de OncoBridge existe pero no es consultable en tiempo real durante la consulta.

### 2.2 Componente 2 — Asistencia Radiológica Médicas

Una vez que el paciente es derivado al especialista en imágenes, este debe leer estudios complejos (tomografías, resonancias, ecografías) sin contexto clínico estructurado del paso anterior. Los desafíos incluyen:

- Pérdida del contexto clínico previo: el radiólogo recibe el estudio pero no las hipótesis diagnósticas del oncólogo.
- Tiempo de reporte elevado por ausencia de orientación sobre qué zonas priorizar.
- Imposibilidad de consultar en tiempo real qué patrón de imagen corresponde a cada hipótesis diagnóstica.

### 2.3 El Problema Central: Conocimiento Inaccesible en el Punto de Decisión

OncoBridge dispone de una base de conocimiento oncológico curada con miles de entradas — cada una describiendo biomarcadores, presentaciones clínicas, factores de riesgo, patrones de imagen esperados y guías para el radiólogo. **Es una de las bases más completas de la industria.** Sin embargo, ningún médico puede consultarla manualmente durante una consulta de minutos o una lectura de imagen bajo presión de tiempo.

Esta brecha — conocimiento disponible pero inaccesible en el momento que importa — es el problema central que OncoBridge AI viene a resolver. Los datos cuantifican el costo de no resolverlo:

El **retraso diagnóstico tiene impacto directo en mortalidad**: cada mes de demora en el tratamiento oncológico se asocia con [6–8% de incremento en riesgo de mortalidad](https://pubmed.ncbi.nlm.nih.gov/33148535/) (revisión sistemática de 209 estudios). Una demora de 4 semanas [aumenta ese riesgo hasta un 13%](https://www.cancercenter.com/community/blog/2024/07/delayed-cancer-treatment-risks); a las 12 semanas, el hazard ratio alcanza 1.39. En tumores sólidos diagnosticados en estadio temprano, los retrasos prolongados [se asocian con hasta un 23% mayor riesgo de muerte](https://pubmed.ncbi.nlm.nih.gov/34258389/).

El **estadio al diagnóstico es el predictor más fuerte de sobrevida**: [pacientes en estadio avanzado (III–IV) tienen casi siete veces más riesgo de mortalidad](https://www.frontiersin.org/journals/public-health/articles/10.3389/fpubh.2014.00087/full) que los diagnosticados temprano. Cada semana de demora en el triage puede significar un estadio más avanzado al momento del diagnóstico.

Los **tiempos de espera actuales son sistemáticamente largos**: en el NHS del Reino Unido, [solo el 67–70% de los pacientes inicia tratamiento dentro de los 2 meses de una derivación urgente](https://www.rcr.ac.uk/news-policy/latest-updates/cancer-and-diagnostic-waiting-times-for-september-2024/) (dato de 2024–2025), contra una meta del 85%. Más de 65.000 pacientes esperaron más de un mes para recibir resultados diagnósticos en ese período.

Los **especialistas en imágenes están al límite de su capacidad**: entre 2009 y 2020, [la carga de trabajo de los radiólogos creció un 80%](https://pubmed.ncbi.nlm.nih.gov/41456840/). El [déficit en EE.UU. se estima en 1.500–3.100 profesionales, con el 50% de los puestos vacantes sin cubrir](https://www.acr.org/Clinical-Resources/Publications-and-Research/ACR-Bulletin/Radiology-Workforce-Shortage-and-Growing-Demand-Something-Has-to-Give). Los radiólogos más exigidos leen hasta 73.9 estudios por día, y el [44–80% reporta síntomas de burnout](https://www.diagnosticimaging.com/view/burnout-in-radiology-key-risk-factors-promising-solutions).

### 2.4 Impacto Clínico Esperado

La implementación de OncoBridge AI apunta a reducir los tiempos de triage, mejorar la consistencia diagnóstica y optimizar el uso de recursos de imagen, haciendo que el conocimiento de la base de OncoBridge llegue a cada médico en cada consulta — de forma automática, estructurada y accionable.

---

## 3. Por Qué Tiene Valor lo Aprendido

Este proyecto es un vehículo de aprendizaje en IA Generativa aplicada a un dominio de alto impacto y alta complejidad. Las competencias desarrolladas trascienden el ejercicio académico.

### 3.1 Relevancia en el Ecosistema de IA Médica

Los sistemas de IA de soporte a la decisión clínica (Clinical Decision Support Systems — CDSS) representan uno de los mercados de mayor crecimiento en health tech. Comprender cómo diseñar, evaluar y limitar estos sistemas es una habilidad fundamental para cualquier profesional que trabaje en la intersección de la IA y la salud.

El proyecto también desarrolla pensamiento crítico sobre las limitaciones de la IA generativa en contextos clínicos: alucinaciones, sesgos de datos, calibración de confianza y la importancia de mantener al médico como tomador de decisión final.

### 3.2 Competencias a Demostrar

El trabajo final es la oportunidad de demostrar la capacidad de ir desde un problema clínico real hasta un sistema funcional evaluable: diseñar la solución, implementarla, medirla críticamente y comunicar los aprendizajes de manera clara.

---

## 4. Contrato del Sistema — Inputs y Outputs

La interfaz primaria de interacción con el sistema es un documento **JSON estructurado**. Este contrato define qué debe recibir y qué debe producir cada componente del sistema. La implementación interna de cómo se llega de un punto al otro es decisión del equipo.

El uso de JSON como interfaz tiene dos implicancias prácticas importantes. Primero, simplifica la integración con sistemas externos (historia clínica electrónica, laboratorio, PACS). Segundo, hace que el dataset de evaluación sea directamente ejecutable: cada caso de test es un par `{input.json, expected_output.json}` que puede correrse de forma automatizada contra el sistema.

### 4.0 Requerimientos No Funcionales

El sistema debe respetar las restricciones definidas por este contrato de inputs/outputs y mantener la separación en dos componentes que colaboran de manera secuencial (Componente 1 → Componente 2). Más allá de eso, el equipo tiene libertad para decidir la arquitectura interna, pero debe **justificar** sus decisiones considerando restricciones reales del contexto clínico:

- **El sistema asiste, no reemplaza:** en ningún momento el sistema toma decisiones diagnósticas autónomas. Cada output es una recomendación de apoyo — la decisión clínica final recae siempre en el médico especialista. La interfaz debe dejar esto claro al usuario en todo momento.
- **Interfaz para usuarios no técnicos:** la interfaz con la que interactúan el oncólogo y el especialista en imágenes debe estar diseñada para **personas no técnicas**. Nada de JSON crudo, logs, ni configuraciones técnicas visibles al usuario final: los outputs del sistema deben presentarse de forma clara, accionable y adaptada al flujo clínico de cada perfil.
- **Eficiencia de contexto — restricción crítica del negocio:** OncoBridge opera con un LLM corporativo de contexto limitado. Esta no es una recomendación de buenas prácticas — es una restricción técnica real que define si el sistema puede funcionar en producción o no. La base de ground truth oncológico tiene miles de entradas que no caben en un contexto, el historial clínico de un paciente puede ser extenso, y el sistema debe procesar múltiples hipótesis simultáneamente. **La eficiencia en el uso del contexto es un factor de éxito tan crítico como la precisión diagnóstica.** Se espera que el equipo demuestre cómo gestiona esta restricción: qué se incluye y qué se omite del historial, cómo el RAG selecciona y comprime las entradas del ground truth antes de pasarlas al modelo, uso de caching, resumen progresivo del contexto, selección del modelo adecuado por tarea, y cualquier otra estrategia orientada a maximizar calidad dentro del límite de tokens disponible.

---

### 4.1 Base de Conocimiento — Ground Truth Oncológico

El sistema cuenta con una **base de ground truth oncológico** que actúa como conocimiento de referencia para el Componente 1. Esta base es un conjunto de entradas JSON, cada una describiendo un tipo de condición oncológica o diagnóstico diferencial relevante, con toda la información necesaria para que el sistema pueda matchear el caso clínico de un paciente contra la base y producir hipótesis diagnósticas calibradas.

> **Restricción de contexto:** La base de ground truth puede contener **cientos o miles de entradas** y no puede cargarse completa en el contexto del LLM corporativo. El equipo debe diseñar una estrategia para resolver esta restricción. Cómo lo hacen es decisión del equipo y parte de los criterios de evaluación.

Cada entrada del ground truth tiene un identificador único (`gt_id`) y está estructurada en cuatro secciones: datos objetivos (`objective_data`), datos subjetivos (`subjective_data`), guía para el radiólogo (`radiologist_guidance`) y metadatos de probabilidad (`base_probability`, `urgency_level`, `notes`).

**Estructura de una entrada del Ground Truth:**

```jsonc
{
  // Identificador único de esta entrada en la base. El sistema lo devuelve en el output
  // de Componente 1 para indicar qué condición matcheó. Formato: GT-<CÓDIGO>-<NÚMERO>.
  "gt_id": "GT-LUNG-001",

  // Código ICD-10: estándar internacional de clasificación de enfermedades.
  // Permite interoperabilidad con sistemas de historia clínica electrónica (HCE).
  "icd_10": "C34.1",

  // Descripción oficial del código ICD-10. Se devuelve en el output de Componente 1
  // en lugar de un nombre libre, garantizando consistencia terminológica.
  // C34.1 = neoplasia maligna del lóbulo superior, bronquio o pulmón.
  "icd_10_description": "Neoplasia maligna del lóbulo superior del pulmón",

  // Datos objetivos y medibles: resultados de laboratorio, hallazgos al examen físico
  // y factores de riesgo verificables. El RAG usa estos campos para matchear contra
  // los datos clínicos del paciente (labs, hallazgos, antecedentes).
  "objective_data": {

    // Marcadores tumorales y valores de laboratorio característicos de esta condición.
    // Se expresan como umbrales o rangos, no valores absolutos.
    "biomarkers": {
      "CEA": "> 5 ng/mL (elevado)",                 // Antígeno carcinoembrionario
      "CYFRA_21_1": "> 3.3 ng/mL (elevado)",        // Marcador de carcinoma no microcítico
      "NSE": "elevada (sugiere componente neuroendocrino)", // Enolasa neuronal específica
      "EGFR": "mutación activadora (en adenocarcinoma no escamoso)" // Diana terapéutica
    },

    // Hallazgos objetivos detectados en el examen físico por el médico.
    "clinical_findings": [
      "hipoventilación en campo pulmonar superior derecho",
      "adenopatía supraclavicular palpable",
      "acropaquia (dedos en palillo de tambor)",
      "signos de derrame pleural (matidez, abolición del murmullo vesicular)"
    ],

    // Condiciones previas del paciente que aumentan la probabilidad de este diagnóstico.
    "risk_factors": [
      "tabaquismo activo o ex-tabaquismo (> 20 paquetes-año)",
      "exposición ocupacional a asbesto o radón",
      "EPOC o fibrosis pulmonar previa",
      "edad > 55 años",
      "nódulo pulmonar indeterminado en TC previa"
    ],

    // Hallazgos en estudios de imagen previos que, si están presentes, elevan
    // significativamente la sospecha de esta condición.
    "prior_imaging_red_flags": [
      "Lung-RADS 4 en TC de screening previa",
      "nódulo sólido nuevo no presente en estudio anterior",
      "crecimiento del nódulo respecto a control previo (tiempo de duplicación < 400 días)"
    ]
  },

  // Datos subjetivos: síntomas reportados por el paciente y patrón de evolución.
  // Complementan los datos objetivos — solos no son diagnósticos, pero orientan el match.
  "subjective_data": {

    // Síntomas que el paciente describe en la consulta (voz del paciente normalizada).
    "symptoms": [
      "tos persistente (> 3 semanas) que cambió de patrón",
      "hemoptisis (expectoración con sangre)",
      "disnea de esfuerzo progresiva",
      "dolor torácico persistente",
      "pérdida de peso no intencional"
    ],

    // Frases literales o paráfrasis de cómo el paciente describe su problema.
    // Útil para el RAG cuando el input viene de lenguaje natural (voz o texto libre).
    "patient_reported_concerns": [
      "tengo una tos que no se me va hace más de un mes",
      "escupí sangre un par de veces",
      "me falta el aire para cosas que antes hacía sin problema"
    ],

    // Cómo evolucionó el cuadro en el tiempo. Ayuda a distinguir condiciones agudas
    // (neumonía) de crónicas o progresivas (cáncer).
    "onset_pattern": "aparición progresiva en semanas a meses, sin resolución espontánea"
  },

  // Instrucciones para el radiólogo generadas a partir de esta entrada del ground truth.
  // El Componente 1 copia y adapta este bloque en su output cuando matchea este gt_id.
  "radiologist_guidance": {

    // Modalidades de imagen recomendadas, ordenadas de mayor a menor prioridad.
    "modality_priority": ["chest_CT_contrast", "PET_CT", "chest_MRI"],

    // Proyecciones o vistas específicas a solicitar dentro de cada modalidad.
    "views_recommended": ["cortes axiales de tórax con contraste", "reconstrucción coronal y sagital", "ventana de parénquima y ventana de mediastino"],

    // Dónde debe enfocar el radiólogo su análisis: región corporal, landmarks anatómicos
    // y zonas prioritarias. Este bloque orienta la lectura antes de abrir el estudio.
    "imaging_location": {
      "body_region": "tórax con foco en lóbulo superior derecho",
      "anatomical_landmarks": "lóbulo superior derecho, hilio pulmonar derecho, mediastino (estaciones ganglionares 4R y 7), pleura adyacente",
      // Si es true, el radiólogo debe comparar ambos campos pulmonares para detectar asimetrías.
      "bilateral_comparison_required": true,
      "priority_zones": [
        "nódulo o masa espiculada en lóbulo superior derecho reportada por el clínico",
        "ganglios mediastinales e hiliares (estaciones 4R, 7 y 10R)",
        "superficie pleural y senos costofrénicos como zona de extensión posible"
      ],
      // Indicaciones técnicas de posicionamiento y adquisición del estudio.
      "positioning_notes": "TC helicoidal de tórax con contraste endovenoso, cortes finos (≤ 1.25 mm). Adquirir fase venosa para caracterización mediastinal. Reconstruir en ventana de parénquima y de mediastino. Extender el rango a suprarrenales si se sospecha diseminación."
    },

    // Descripción de lo que el radiólogo debería encontrar si el diagnóstico es correcto.
    // Funciona como "qué buscar" — orienta la lectura del estudio real.
    "expected_imaging_findings": "Masa o nódulo espiculado de partes blandas en lóbulo superior derecho, con retracción pleural (pleural tag) y broncograma aéreo. Posible linfangitis carcinomatosa y adenopatías mediastinales/hiliares > 1 cm en eje corto. En casos avanzados: derrame pleural o nódulos satélite.",

    // Prompt positivo para MedDiffusion: describe los hallazgos visuales que debe
    // generar el modelo de difusión para producir una imagen de referencia ilustrativa.
    "meddiffusion_prompt": "High-resolution contrast-enhanced chest CT, axial view, spiculated soft-tissue mass in right upper lobe, pleural retraction, air bronchogram, enlarged mediastinal and hilar lymph nodes, high suspicion malignancy Lung-RADS 4X, clinical medical imaging",

    // Prompt negativo para MedDiffusion: rasgos visuales que NO deben aparecer
    // en la imagen generada (evita que el modelo produzca hallazgos benignos).
    "meddiffusion_negative_prompt": "benign, smooth well-defined nodule, popcorn calcification, homogeneous consolidation, normal lung parenchyma",

    // Instrucciones adicionales de composición para guiar la generación de imagen.
    "image_generation_notes": "Generar corte axial de TC de tórax en ventana de parénquima con masa espiculada en lóbulo superior derecho y retracción pleural. Incluir una vista en ventana de mediastino que evidencie adenopatías. El contraste y nivel de detalle deben ser consistentes con TC multidetector con contraste."
  },

  // Probabilidad a priori de este diagnóstico dado el perfil general de síntomas
  // y datos de esta entrada. El sistema la ajusta con los datos concretos del paciente
  // para producir la match_probability final en el output.
  "base_probability": 0.78,

  // Nivel de urgencia clínica si se confirma este diagnóstico. Valores: "alta", "media", "baja".
  // Determina el campo "urgency" en el output del Componente 1.
  "urgency_level": "alta",

  // Observaciones clínicas adicionales para el médico. Texto libre, no procesado por el modelo.
  "notes": "Considerar derivación urgente a cirugía torácica y estadificación con PET-CT si la probabilidad de match supera 0.75 y hay adenopatía supraclavicular palpable."
}
```

El campo `base_probability` representa la probabilidad a priori de que un paciente con el perfil de síntomas y datos clínicos de esta entrada efectivamente tenga este diagnóstico. Es el punto de partida que el sistema ajusta con los datos concretos del paciente para producir la probabilidad final reportada en el output.

A continuación se muestra un segundo ejemplo de entrada para ilustrar cómo se define una condición benigna que actúa como diagnóstico diferencial. El RAG es el responsable de recuperar entradas similares — no existen punteros explícitos entre entradas de la base:

```jsonc
{
  // Identificador único. Las entradas de la base no son solo oncológicas —
  // incluyen diagnósticos diferenciales benignos para que el sistema pueda
  // descartar activamente condiciones que se parecen al cáncer.
  "gt_id": "GT-PNEUMONIA-001",

  // ICD-10: J18.1 = neumonía lobar, organismo no especificado.
  // El prefijo J (sistema respiratorio) vs. C (neoplasias) ya diferencia
  // semánticamente esta entrada de las oncológicas.
  "icd_10": "J18.1",

  // Descripción oficial ICD-10. El sistema la devuelve en el output para que
  // el médico vea el diagnóstico diferencial con terminología estandarizada.
  "icd_10_description": "Neumonía lobar de la comunidad (diagnóstico diferencial benigno)",

  // Datos objetivos. En neumonía los biomarcadores tumorales son normales —
  // su ausencia es un dato tan relevante como su presencia en GT-LUNG-001.
  "objective_data": {
    "biomarkers": {
      "CEA": "normal (< 5 ng/mL)",         // Ausencia de marcador tumoral
      "CYFRA_21_1": "normal (< 3.3 ng/mL)", // Ausencia de marcador tumoral
      "leucocitos": "elevados (leucocitosis > 11.000/μL con neutrofilia)", // Infección activa
      "PCR": "elevada (> 100 mg/L en neumonía bacteriana)",  // Reactante de fase aguda
      "procalcitonina": "elevada (sugiere etiología bacteriana)" // Orienta a infección bacteriana
    },

    // Hallazgos físicos. Notar el contraste con GT-LUNG-001:
    // aquí hay fiebre y signos de condensación aguda — ausentes en el cáncer.
    "clinical_findings": [
      "fiebre > 38.5°C con escalofríos",
      "crepitantes y estertores en el campo pulmonar afectado",
      "soplo tubárico y matidez a la percusión (condensación)",
      "taquipnea y taquicardia",
      "ausencia de acropaquia y de adenopatía dura" // Diferente al cáncer establecido
    ],

    // Factores de riesgo específicos de neumonía. Muy distintos a los del cáncer,
    // lo que ayuda al RAG a discriminar entre ambas entradas.
    "risk_factors": [
      "infección respiratoria viral reciente",
      "EPOC o asma",
      "tabaquismo",
      "inmunosupresión",
      "broncoaspiración (alteración de la deglución)"
    ],

    // Sin red flags en imagen previa — la neumonía no tiene precursores imagenológicos.
    "prior_imaging_red_flags": []
  },

  // Datos subjetivos. El onset agudo (días) es el rasgo más diferenciador
  // respecto al cáncer (semanas a meses).
  "subjective_data": {
    "symptoms": [
      "tos productiva con expectoración purulenta de aparición aguda (< 1 semana)",
      "fiebre alta con escalofríos",
      "dolor pleurítico (dolor al respirar profundo)", // Diferente al dolor sordo del tumor
      "disnea de aparición reciente",
      "malestar general y astenia"
    ],

    // Frases del paciente que orientan al RAG cuando el input es texto libre.
    "patient_reported_concerns": [
      "empecé de golpe con fiebre y flema verde",
      "me duele el pecho cuando respiro hondo",
      "tengo fiebre y escalofríos desde hace dos días"
    ],

    // Onset agudo + respuesta a antibióticos = clave diferenciadora de malignidad.
    "onset_pattern": "aparición aguda en días, frecuentemente tras un cuadro viral. Responde a antibióticos en 48-72 hs."
  },

  // Guía para el radiólogo. En neumonía la primera línea es la radiografía de tórax,
  // no la TC — el sistema debe reflejar esta diferencia en su output.
  "radiologist_guidance": {
    "modality_priority": ["chest_Xray", "chest_CT_contrast"], // La TC solo si no hay respuesta o para descartar masa subyacente
    "views_recommended": ["radiografía de tórax PA y lateral", "TC de tórax con contraste si la condensación persiste tras el tratamiento"],

    // Localización: guiada por los síntomas clínicos, no por zona anatómica fija.
    "imaging_location": {
      "body_region": "campo pulmonar afectado (segmento con condensación referida por el clínico)",
      "anatomical_landmarks": "segmento o lóbulo con crepitantes, espacio pleural adyacente, árbol bronquial regional",
      // No se requiere comparación bilateral en una condensación unilateral.
      "bilateral_comparison_required": false,
      "priority_zones": [
        "área de condensación clínica",
        "senos costofrénicos para descartar derrame paraneumónico",
        "hilios para descartar masa endobronquial subyacente"
      ],
      "positioning_notes": "Radiografía PA y lateral en inspiración máxima. Si se realiza TC: cortes con contraste para diferenciar consolidación de masa central. Documentar broncograma aéreo (favorece neumonía) y descartar atelectasia obstructiva."
    },

    // Hallazgos esperados: consolidación del espacio aéreo, sin masa espiculada. La ausencia
    // de masa espiculada de partes blandas es el hallazgo más importante para descartar cáncer.
    "expected_imaging_findings": "Consolidación del espacio aéreo con broncograma aéreo, de límites segmentarios o lobares, sin masa espiculada de partes blandas. Puede asociar derrame pleural paraneumónico. Ausencia de retracción pleural espiculada y de adenopatías mediastinales voluminosas.",

    // Prompt positivo: patrón de consolidación para MedDiffusion.
    "meddiffusion_prompt": "Contrast-enhanced chest CT, axial view, lobar air-space consolidation with air bronchogram, patent bronchi, no spiculated soft-tissue mass, community-acquired pneumonia pattern, clinical medical imaging",

    // Prompt negativo: excluir explícitamente los rasgos malignos.
    "meddiffusion_negative_prompt": "spiculated mass, pleural retraction, lymphangitic pattern, enlarged mediastinal nodes, malignant",

    "image_generation_notes": "Generar corte axial de TC de tórax mostrando consolidación con broncograma aéreo de distribución lobar, sin masa sólida espiculada. Si se incluye derrame: colección pleural laminar en el seno costofrénico."
  },

  // Probabilidad a priori más baja que GT-LUNG-001 en contexto oncológico —
  // la neumonía es menos probable que el cáncer en un paciente de alto riesgo.
  "base_probability": 0.41,

  "urgency_level": "media", // Media: requiere tratamiento, pero no es emergencia oncológica

  // Nota clínica crítica: cuándo esta entrada deja de ser el diagnóstico correcto
  // y el sistema debe escalar a una hipótesis oncológica.
  "notes": "Si la consolidación no se resuelve tras 6-8 semanas de tratamiento antibiótico adecuado, considerar TC y broncoscopía/biopsia para descartar carcinoma con patrón de neumonía obstructiva (GT-LUNG-001). La consolidación persistente en fumador mayor de 50 años debe tratarse con alta sospecha oncológica."
}
```

---

### 4.2 Componente 1 — Análisis Clínico

Este componente recibe el contexto del paciente y produce una evaluación diagnóstica preliminar, incluyendo una probabilidad de necesidad de derivación a estudios de imagen.

**Input:**

```json
{
  "patient_id": "PAT-00123",
  "demographics": {
    "age": 64,
    "sex": "M",
    "smoking_history": "35 paquetes-año, ex-tabaquista hace 2 años",
    "family_history": ["lung_cancer"]
  },
  "current_symptoms": [
    "tos persistente de 5 semanas que cambió de características",
    "dos episodios de hemoptisis leve",
    "pérdida de peso de 4 kg no intencional en 2 meses"
  ],
  "medical_history": [
    {
      "date": "2019-06",
      "event": "EPOC moderada diagnosticada por espirometría"
    },
    {
      "date": "2023-11",
      "event": "TC de tórax de baja dosis (screening) — Lung-RADS 2, sin nódulos sospechosos"
    }
  ],
  "current_labs": {
    "CEA": 6.9,
    "CYFRA_21_1": 4.1,
    "hemograma": "anemia normocítica leve"
  }
}
```

**Output esperado:**

```json
{
  "patient_id": "PAT-00123",
  "clinical_summary": "Síntesis clínica del paciente generada por el sistema.",

  "matched_ground_truths": [
    {
      "gt_id": "GT-LUNG-001",
      "icd_10": "C34.1",
      "icd_10_description": "Neoplasia maligna del lóbulo superior del pulmón",
      "match_probability": 0.88,
      "match_rationale": "Paciente masculino de 64 años, ex-tabaquista de 35 paquetes-año, con tos de 5 semanas que cambió de patrón, hemoptisis y pérdida de peso. CEA y CYFRA 21-1 elevados. El perfil de riesgo y la nueva sintomatología respiratoria justifican esta como hipótesis principal.",
      "radiologist_instructions": {
        "suggested_modalities": ["chest_CT_contrast", "PET_CT"],
        "imaging_location": {
          "body_region": "tórax con foco en lóbulo superior derecho",
          "anatomical_landmarks": "lóbulo superior derecho, hilio pulmonar derecho, mediastino (estaciones 4R y 7)",
          "bilateral_comparison_required": true,
          "priority_zones": [
            "nódulo o masa espiculada en lóbulo superior derecho",
            "ganglios mediastinales e hiliares (estaciones 4R, 7 y 10R)"
          ],
          "positioning_notes": "TC de tórax con contraste, cortes finos ≤ 1.25 mm, ventana de parénquima y de mediastino. Extender a suprarrenales si se sospecha diseminación."
        },
        "clinical_context_for_radiologist": "Paciente de 64 años, ex-tabaquista de alto riesgo, con tos que cambió de patrón, hemoptisis y pérdida de peso. Buscar masa espiculada, retracción pleural, broncograma aéreo y adenopatías mediastinales.",
        "meddiffusion_reference_prompt": "High-resolution contrast-enhanced chest CT, axial view, spiculated soft-tissue mass in right upper lobe, pleural retraction, air bronchogram, enlarged mediastinal and hilar lymph nodes, high suspicion malignancy Lung-RADS 4X, clinical medical imaging",
        "meddiffusion_negative_prompt": "benign, smooth well-defined nodule, popcorn calcification, homogeneous consolidation, normal lung parenchyma",
        "reference_images_note": "Imágenes de referencia MedDiffusion para GT-LUNG-001. Usar como orientación visual, no como diagnóstico."
      }
    },
    {
      "gt_id": "GT-HAMARTOMA-001",
      "icd_10": "D14.3",
      "icd_10_description": "Neoplasia benigna de bronquio y pulmón",
      "match_probability": 0.24,
      "match_rationale": "El antecedente de nódulo pulmonar en screening previo obliga a considerar un hamartoma como diferencial benigno, aunque la probabilidad es menor dado el perfil de riesgo oncológico elevado.",
      "radiologist_instructions": {
        "suggested_modalities": ["chest_CT", "PET_CT"],
        "imaging_location": {
          "body_region": "lóbulo superior derecho",
          "anatomical_landmarks": "nódulo pulmonar reportado, parénquima circundante",
          "bilateral_comparison_required": false,
          "priority_zones": [
            "nódulo pulmonar en lóbulo superior derecho",
            "comparación con TC de screening previa (2023)"
          ],
          "positioning_notes": "TC de tórax sin y con contraste. Evaluar densidad interna: la presencia de grasa y calcificación en palomita de maíz (popcorn) orienta a hamartoma."
        },
        "clinical_context_for_radiologist": "Descartar hamartoma como alternativa benigna. Buscar nódulo redondeado, bordes lisos, con grasa interna y calcificación en popcorn, sin retracción pleural ni espiculación.",
        "meddiffusion_reference_prompt": "Chest CT, axial view, well-circumscribed rounded pulmonary nodule with popcorn calcification and internal fat density, smooth margins, benign hamartoma appearance, clinical medical imaging",
        "meddiffusion_negative_prompt": "spiculated, irregular margins, pleural retraction, lymphangitic spread, malignant",
        "reference_images_note": "Imágenes de referencia MedDiffusion para GT-HAMARTOMA-001. Patrón benigno esperado en caso de hamartoma."
      }
    }
  ],

  "imaging_needed_probability": 0.88,
  "reasoning": "Explicación del razonamiento clínico integrado del sistema, considerando los ground truths recuperados y los datos del paciente.",
  "recommendation": "DERIVAR_A_IMAGEN",
  "urgency": "alta",
  "conclusive": true,

  "token_usage": {
    "prompt_tokens": 1847,
    "completion_tokens": 534,
    "total_tokens": 2381,
    "model": "claude-sonnet-4-6",
    "retrieved_gt_entries": 5,
    "gt_entries_in_context": 2
  }
}
```

El output también puede ser **no conclusivo**, cuando el sistema no encuentra suficiente evidencia para sostener ninguna hipótesis diagnóstica. En ese caso `matched_ground_truths` es un array vacío, `conclusive` es `false`, y `recommendation` toma el valor `SIN_ELEMENTOS_PARA_EVALUAR`:

```json
{
  "patient_id": "PAT-00456",
  "clinical_summary": "Paciente sin síntomas específicos ni datos de laboratorio que orienten a patología oncológica.",
  "matched_ground_truths": [],
  "imaging_needed_probability": 0.04,
  "reasoning": "Los datos clínicos disponibles no presentan correspondencia suficiente con ninguna entrada de la base de ground truth. No se identifican síntomas, biomarcadores ni factores de riesgo que justifiquen una hipótesis diagnóstica oncológica.",
  "recommendation": "SIN_ELEMENTOS_PARA_EVALUAR",
  "urgency": "ninguna",
  "conclusive": false,
  "token_usage": {
    "prompt_tokens": 943,
    "completion_tokens": 187,
    "total_tokens": 1130,
    "model": "claude-sonnet-4-6",
    "retrieved_gt_entries": 3,
    "gt_entries_in_context": 3
  }
}
```

Los campos clave del output son:

- **`matched_ground_truths`:** Array ordenado por `match_probability` descendente. Puede tener uno o más elementos, o estar vacío si el output es no conclusivo. Cada elemento incluye el `gt_id`, el código y descripción ICD-10, la probabilidad de match con su justificación, y sus propias `radiologist_instructions` — porque cada diagnóstico diferencial requiere modalidades, zonas de foco y prompts de MedDiffusion distintos.
- **`conclusive`:** Booleano que indica si el sistema pudo formular al menos una hipótesis diagnóstica sostenida por los datos del paciente. Un output no conclusivo es información clínicamente válida: le dice al médico que el cuadro no orienta a oncología con los datos disponibles.
- **`imaging_needed_probability`:** Probabilidad estimada de que el paciente requiera un estudio de imagen. **Este valor no lo estima libremente el LLM — el equipo debe definir explícitamente la función de cálculo.** Una forma razonable es una combinación ponderada de las `match_probability` de los ground truths matcheados y sus respectivos `urgency_level` y `base_probability`. El equipo debe documentar y justificar la fórmula elegida en el README y en la presentación: qué variables entran, qué peso tiene cada una y por qué. Un LLM que produce este número de forma opaca sin una función definida no cumple el contrato.
- **`token_usage`:** Consumo de tokens de la invocación al LLM. Incluye cuántas entradas del ground truth se recuperaron por RAG y cuántas se incluyeron finalmente en el contexto. Campo obligatorio para medir eficiencia del sistema.

**Valores posibles de los campos enumerados:**

| Campo | Valores posibles | Descripción |
|---|---|---|
| `recommendation` | `DERIVAR_A_IMAGEN` | Hay evidencia suficiente para justificar un estudio de imagen |
| | `NO_DERIVAR` | Los datos no justifican derivación a imagen en este momento |
| | `SEGUIMIENTO_CLINICO` | Sin urgencia de imagen, pero se recomienda seguimiento en consulta |
| | `SIN_ELEMENTOS_PARA_EVALUAR` | Datos insuficientes o no concluyentes para formular una recomendación |
| `urgency` | `alta` | Derivación en menos de 48-72 hs |
| | `media` | Derivación en días a semanas según disponibilidad |
| | `baja` | Derivación programada sin urgencia clínica |
| | `ninguna` | No aplica (output no conclusivo o sin derivación) |
| `conclusive` | `true` | El sistema pudo formular al menos una hipótesis diagnóstica |
| | `false` | Los datos no permitieron identificar ningún match en el ground truth |

---

### 4.3 Componente 2 — Asistencia Radiológica

Este componente está diseñado para asistir al **especialista en imágenes (radiólogo)** en su lectura del estudio. Su función no es reemplazar al radiólogo sino orientar su atención: dado que el Componente 1 ya identificó las hipótesis diagnósticas más probables y las zonas anatómicas de interés, el Componente 2 le comunica al radiólogo qué buscar, dónde mirarlo y cómo debería verse si la hipótesis es correcta — usando como referencia las imágenes generadas con MedDiffusion a partir del ground truth matcheado.

El componente recibe el output completo del Componente 1 (con los `matched_ground_truths` y sus `radiologist_instructions`) junto con el estudio de imagen del paciente, y produce un informe diagnóstico estructurado que contrasta lo que el sistema esperaba encontrar con lo que efectivamente aparece en la imagen.

**Input:**

```json
{
  "component_1_output": {
    "patient_id": "PAT-00123",
    "clinical_summary": "...",
    "matched_ground_truths": [
      {
        "gt_id": "GT-LUNG-001",
        "icd_10": "C34.1",
        "icd_10_description": "Neoplasia maligna del lóbulo superior del pulmón",
        "match_probability": 0.88,
        "radiologist_instructions": {
          "suggested_modalities": ["chest_CT_contrast", "PET_CT"],
          "imaging_location": {
            "body_region": "tórax con foco en lóbulo superior derecho",
            "anatomical_landmarks": "lóbulo superior derecho, hilio derecho, mediastino (estaciones 4R y 7)",
            "bilateral_comparison_required": true,
            "priority_zones": ["masa espiculada en lóbulo superior derecho", "ganglios mediastinales 4R y 7"],
            "positioning_notes": "..."
          },
          "clinical_context_for_radiologist": "...",
          "meddiffusion_reference_prompt": "High-resolution contrast-enhanced chest CT, axial view, spiculated soft-tissue mass in right upper lobe...",
          "meddiffusion_negative_prompt": "benign, smooth well-defined nodule, popcorn calcification, homogeneous consolidation, normal lung parenchyma"
        }
      },
      {
        "gt_id": "GT-HAMARTOMA-001",
        "icd_10": "D14.3",
        "icd_10_description": "Neoplasia benigna de bronquio y pulmón",
        "match_probability": 0.24,
        "radiologist_instructions": {
          "suggested_modalities": ["chest_CT"],
          "imaging_location": {
            "body_region": "lóbulo superior derecho, nódulo pulmonar",
            "anatomical_landmarks": "lóbulo superior derecho",
            "bilateral_comparison_required": false,
            "priority_zones": ["nódulo pulmonar en lóbulo superior derecho"],
            "positioning_notes": "..."
          },
          "clinical_context_for_radiologist": "...",
          "meddiffusion_reference_prompt": "Chest CT, well-circumscribed rounded pulmonary nodule with popcorn calcification and internal fat density...",
          "meddiffusion_negative_prompt": "spiculated, irregular margins, pleural retraction, malignant"
        }
      }
    ],
    "imaging_needed_probability": 0.88,
    "recommendation": "DERIVAR_A_IMAGEN",
    "urgency": "alta"
  },
  "imaging_study": {
    "modality": "chest_CT",
    "view": "axial con contraste, cortes de 1.25 mm",
    "image_path": "studies/PAT-00123/tc_torax_20260415.png",
    "acquisition_date": "2026-04-15"
  }
}
```

**Output esperado:**

```json
{
  "patient_id": "PAT-00123",
  "segmentation": {
    "regions_of_interest": [
      {
        "id": "ROI-01",
        "location": "lóbulo superior derecho",
        "size_mm": 26.0,
        "shape": "irregular",
        "margins": "espiculados",
        "density": "partes blandas"
      }
    ]
  },
  "findings": "Descripción estructurada de los hallazgos por región anatómica, contrastando lo esperado según el ground truth con lo observado en la imagen.",
  "classification": "sospechoso",
  "confidence": 0.91,
  "final_recommendation": "Recomendación clínica final del sistema.",
  "next_steps": ["biopsia_transtoracica_guiada_por_TC", "PET_CT_estadificacion", "consulta_cirugia_toracica"],
  "token_usage": {
    "prompt_tokens": 2134,
    "completion_tokens": 612,
    "total_tokens": 2746,
    "model": "claude-sonnet-4-6"
  }
}
```

---

### 4.4 Estructura del Dataset de Evaluación

El hecho de que la interfaz sea JSON hace que la evaluación sea completamente automatizable. El dataset tiene dos componentes separados: la **base de ground truth oncológico** (conocimiento de referencia del sistema) y los **casos de test clínicos** (pares input/expected para evaluar el output).

```
test_dataset/
│
├── oncology_ground_truth_base/       ← Base de conocimiento del sistema (RAG source)
│   ├── GT-LUNG-001.json              ← Entrada: Adenocarcinoma de pulmón
│   ├── GT-LUNG-002.json              ← Entrada: Carcinoma escamoso de pulmón
│   ├── GT-HCC-001.json               ← Entrada: Hepatocarcinoma (CT/MRI abdomen)
│   ├── GT-COLON-001.json             ← Entrada: Carcinoma colorrectal (CT abdomen)
│   ├── GT-HAMARTOMA-001.json         ← Entrada: Hamartoma pulmonar (benigno)
│   ├── GT-PNEUMONIA-001.json         ← Entrada: Neumonía (diferencial benigno)
│   └── ...                           ← Cientos de entradas posibles
│
└── clinical_cases/                   ← Casos de test para evaluación
    ├── case_001/
    │   ├── input.json                ← Input al Componente 1 (datos del paciente)
    │   └── expected_output.json      ← Output esperado con gt_ids correctos y probabilidades
    ├── case_002/
    │   ├── input.json
    │   └── expected_output.json
    └── ...
```

**Estructura del `expected_output.json` de un caso clínico:**

```json
{
  "case_id": "case_001",
  "correct_gt_ids": ["GT-LUNG-001"],
  "acceptable_secondary_gt_ids": ["GT-HAMARTOMA-001"],
  "imaging_needed_ground_truth": true,
  "urgency_ground_truth": "alta",
  "specialist_decision": "DERIVAR_A_IMAGEN",
  "conclusive_ground_truth": true,
  "difficulty": "moderado",
  "notes": "Caso diseñado para evaluar detección de adenocarcinoma de pulmón en paciente ex-tabaquista de alto riesgo con presentación clásica."
}
```

El script de evaluación itera sobre todos los casos clínicos, invoca al sistema con el `input.json`, y compara el output generado contra el `expected_output.json` verificando: (1) si los `gt_id` matcheados están entre los correctos, (2) si la `match_probability` del gt correcto es la más alta, (3) si la `imaging_needed_probability` y la `recommendation` son correctas, y (4) si el `meddiffusion_reference_prompt` del output corresponde al ground truth identificado correctamente.

---

## 5. Dataset de Tests y Evaluación

La robustez del sistema se evalúa mediante un dataset de casos clínicos sintéticos y/o anonimizados, diseñado para cubrir los escenarios diagnósticos más relevantes y desafiantes en oncología.

### 5.1 Composición del Dataset

| Categoría | Descripción | # Casos Mínimos |
|---|---|---|
| True Positive (TP) | Pacientes con patología que efectivamente requirieron imagen | 30 casos |
| True Negative (TN) | Pacientes sin patología que no requirieron imagen | 30 casos |
| False Positive (FP) | Casos borderline con síntomas inespecíficos | 15 casos |
| False Negative (FN) | Casos sutiles de alta complejidad diagnóstica | 15 casos |
| Casos Multimodales | Pacientes con historial complejo + imagen disponible | 20 casos |

### 5.2 Métricas de Evaluación

#### Componente 1 — Análisis Clínico

| Métrica | Descripción |
|---|---|
| Accuracy de Derivación | % de casos donde la recomendación de imagen coincide con el ground truth |
| Sensibilidad (Recall) | % de casos que necesitan imagen y el sistema identifica correctamente |
| Especificidad | % de casos que NO necesitan imagen y el sistema descarta correctamente |
| Coherencia del Razonamiento | Evaluación humana del razonamiento generado (escala 1–5) |
| Precisión de GT Match | % de casos donde el `gt_id` de mayor probabilidad coincide con el diagnóstico correcto |
| Calibración de GT Probability | Correlación entre `match_probability` reportada y frecuencia real de acierto |
| Eficiencia de Tokens | Tokens totales promedio por caso (prompt + completion). Se evalúa si el equipo logra reducir tokens sin degradar accuracy mediante RAG eficiente, resumen de historial y selección de modelo |

#### Componente 2 — Asistencia Radiológica

| Métrica | Descripción |
|---|---|
| Precisión de Segmentación | IoU (Intersection over Union) entre segmentación generada y ground truth |
| Sensibilidad de Hallazgos | % de lesiones presentes que el sistema identifica correctamente |
| Especificidad de Hallazgos | % de regiones normales que el sistema no reporta como patológicas |
| Calidad del Informe | Evaluación por especialista (completitud, precisión, claridad) |
| Concordancia Clínica | Correlación entre recomendación del sistema y diagnóstico del especialista |

#### Sistema Integrado

| Métrica | Descripción |
|---|---|
| Reducción de Tiempo de Triage | Tiempo con sistema vs. sin sistema (benchmark de referencia) |
| Tasa de Imagen Innecesaria | % de imágenes solicitadas para casos que no las requerían |
| Satisfacción del Especialista | NPS / encuesta de usabilidad completada por evaluadores clínicos |

---

## 6. Repositorio GitHub

Todo el código del proyecto debe estar disponible en un **repositorio GitHub privado** con acceso habilitado al docente. El lenguaje de implementación es **Python** (versión 3.10 o superior). La estructura interna es decisión del equipo, pero el repositorio debe incluir obligatoriamente:

- Código de ambos componentes del sistema, ejecutable end-to-end.
- Dataset de evaluación (o instrucciones para generarlo/descargarlo).
- Script de evaluación que corra el dataset y produzca las métricas.
- Archivo `requirements.txt` con todas las dependencias necesarias para reproducir el entorno (`pip install -r requirements.txt` debe ser suficiente para levantar el proyecto).
- `README.md` completo (ver requisitos abajo).

### 6.1 Requisitos del README

- Descripción del proyecto y sus objetivos.
- Diagrama de arquitectura del sistema diseñado por el equipo.
- Limitaciones conocidas del sistema y trabajo futuro.
- Descripción del dataset de evaluación y resultados obtenidos.

La sección más importante del README es la **guía de ejecución**, que debe permitir a cualquier persona con Python 3.10+ correr el sistema desde cero sin asistencia. Debe incluir obligatoriamente:

1. **Instalación de dependencias** — comando exacto para instalar el entorno (`pip install -r requirements.txt` u equivalente).
2. **Configuración de variables de entorno** — cómo setear API keys u otros parámetros necesarios (sin exponer valores reales; usar un archivo `.env.example` como referencia).
3. **Cómo correr el Componente 1** — comando concreto con un ejemplo de input y el output esperado en consola.
4. **Cómo correr el Componente 2** — ídem para el análisis de imágenes.
5. **Cómo correr el flujo end-to-end** — comando único que encadena ambos componentes sobre un caso de ejemplo.
6. **Cómo correr el script de evaluación** — comando para ejecutar el dataset completo y obtener las métricas.

El README debe poder seguirse línea por línea sin contexto previo y producir un resultado visible. Si el corrector no puede correr el sistema en menos de 10 minutos siguiendo el README, se considera que el requisito no está cumplido.

---

## 7. Presentación en Loom — Estructura Requerida

La entrega final consiste en una presentación grabada en Loom con duración recomendada de **15 a 20 minutos**. La presentación debe cubrir las siguientes secciones en orden.

### 7.1 Secciones de la Presentación

| # | Sección | Contenido Esperado |
|---|---|---|
| 1 | **Descripción del Problema** | Contexto clínico, dolor que resuelve el sistema, impacto esperado en la práctica oncológica. |
| 2 | **Por Qué Tiene Valor lo Aprendido** | Reflexión sobre las competencias adquiridas y su relevancia en IA médica y en el mercado. |
| 3 | **Demo Funcional** | Demostración en vivo con al menos dos casos clínicos: uno positivo (requiere imagen) y uno negativo. |
| 4 | **Dataset y Resultados** | Presentación del dataset de evaluación, criterios de diseño y resultados cuantitativos de métricas clave. |
| 5 | **Overview de Arquitectura** | Diagrama del sistema diseñado por el equipo, decisiones de implementación y justificación de las elecciones técnicas. |
| 6 | **Aprendizajes** | Lecciones técnicas y conceptuales, desafíos encontrados, limitaciones del sistema y próximos pasos. |
| 7 | **Experiencia de Usuario y Puesta en Producción** | El sistema está pensado para usuarios **no técnicos**: el oncólogo (Componente 1) y el especialista en imágenes (Componente 2). Se espera que el equipo **defina y presente la experiencia de uso propuesta para ambos perfiles** (cómo interactúan con el sistema, cómo reciben los resultados, cómo se integra a su flujo de trabajo diario). Adicionalmente, el equipo debe decidir y justificar cómo garantizarían la privacidad de los datos de los pacientes (anonimización, cifrado, control de accesos, cumplimiento de HIPAA/GDPR/Ley 26.529, manejo de PHI en prompts y logs) y qué plan seguirían para llevarlo a producción (infraestructura, despliegue, monitoreo, auditoría, validación clínica y plan de contingencia). No se espera una solución única: se evalúa el criterio del equipo para proponer un enfoque viable y adecuado al usuario final. |

> **Formato de Entrega:** Entregar el link del video de Loom y el link del repositorio de GitHub en el formulario de entrega de la materia antes de la fecha indicada por el docente. Ambos links deben estar activos y accesibles al momento de la corrección.

---

## 8. Criterios de Evaluación

| Criterio | Descripción | Peso |
|---|---|---|
| Funcionalidad del Sistema | Los dos componentes funcionan correctamente en un flujo end-to-end demostrable | 25% |
| Calidad de la Evaluación | Dataset bien diseñado, métricas apropiadas y resultados interpretados correctamente | 20% |
| Arquitectura y Código | Decisiones de diseño justificadas, código limpio y repositorio GitHub organizado | 20% |
| Presentación Loom | Claridad, profundidad, demostración efectiva y tiempo adecuado | 20% |
| Análisis Crítico | Identificación honesta de limitaciones, sesgos y trabajo futuro | 15% |

---

## 9. Consideraciones Éticas y Limitaciones

Un aspecto central de la evaluación es la reflexión crítica sobre las limitaciones de la IA Generativa en contextos médicos. El trabajo final debe abordar explícitamente los siguientes puntos.

### 9.1 El Sistema como Herramienta de Apoyo, No de Reemplazo

El sistema está diseñado como una herramienta de apoyo a la decisión clínica (CDSS). La decisión diagnóstica y terapéutica final recae siempre en el médico especialista. El sistema no debe presentarse como un sustituto del juicio clínico.

### 9.2 Riesgos a Considerar

- **Alucinaciones:** el modelo puede generar razonamientos plausibles pero clínicamente incorrectos.
- **Sesgo de datos:** el rendimiento depende fuertemente de la distribución del dataset de entrenamiento.
- **Calibración de confianza:** una probabilidad de 80% no necesariamente refleja 80% de certeza clínica real.
- **Privacidad:** los datos de pacientes deben anonimizarse y procesarse bajo marcos de privacidad vigentes.

