# OncoBridge AI — Monografía del Trabajo Final

**IA Generativa para Biomedicina — Universidad Austral**

---

## 1. Introducción y planteo del problema

La oncología moderna enfrenta un problema que no es de falta de conocimiento, sino de acceso a ese conocimiento en el momento correcto. Las instituciones de salud acumulan bases de datos clínicas extensas —patrones diagnósticos, biomarcadores, guías de imagen— pero ese material rara vez llega al punto donde se toma la decisión: la consulta de pocos minutos con el paciente adelante, o la lectura de un estudio bajo presión de tiempo. Un oncólogo no puede revisar miles de entradas mientras atiende, y un radiólogo suele recibir el estudio sin el contexto clínico que motivó la derivación.

Este proyecto, OncoBridge AI, aborda esa brecha construyendo un sistema de apoyo a la decisión clínica (en inglés, *Clinical Decision Support System* o CDSS) que hace consultable esa base de conocimiento en tiempo real. El sistema recibe el contexto clínico de un paciente, identifica las hipótesis diagnósticas más probables, decide si corresponde derivar a un estudio de imagen y con qué urgencia, y le entrega al especialista en imágenes una guía de lectura orientada al caso concreto.

Es importante encuadrar el alcance desde el principio: el sistema **asiste, no reemplaza**. La decisión diagnóstica y terapéutica final es siempre del médico. Todo el diseño está subordinado a ese principio.

## 2. Objetivos del trabajo

El objetivo general fue diseñar e implementar un sistema funcional, ejecutable de punta a punta, que demuestre cómo la IA generativa puede acercar el conocimiento oncológico al punto de decisión clínica. Los objetivos específicos fueron:

- Construir dos componentes que colaboren de forma secuencial: uno orientado al oncólogo (consulta inicial) y otro al radiólogo (asistencia en la lectura de imágenes).
- Formalizar un contrato claro de entradas y salidas para que el sistema sea predecible y evaluable.
- Diseñar un mecanismo de recuperación de conocimiento que sea explicable y trazable.
- Evaluar el sistema con un conjunto de casos y métricas apropiadas.
- Mantener el rigor ético propio de un dominio médico, documentando limitaciones de forma honesta.

## 3. Arquitectura y decisiones de diseño

### 3.1 Visión general

El sistema se organiza alrededor de una **base de conocimiento oncológica curada** que ambos componentes consultan. El flujo es secuencial: el Componente 1 procesa el caso del paciente y, si determina que se requiere imagen, produce un resumen-puente que el Componente 2 utiliza para orientar la lectura del estudio.

```
Base de conocimiento  ──►  Componente 1 (oncólogo)  ──►  Componente 2 (radiólogo)
   (retrieval)              hipótesis + triage            guía de lectura + informe
```

### 3.2 La decisión de diseño más importante

La decisión conceptual central del proyecto fue **separar la lógica clínica de la generación de lenguaje**. En muchos sistemas basados en modelos de lenguaje se le pide al modelo que "razone" el diagnóstico directamente, lo que abre la puerta a alucinaciones: el modelo puede producir un razonamiento que suena correcto pero es clínicamente falso. En un dominio médico, ese riesgo es inaceptable.

Por eso, en OncoBridge AI:

- **La lógica clínica** —qué hipótesis considerar, si se requiere imagen, qué urgencia asignar— proviene de la **recuperación (retrieval) sobre la base de conocimiento curada**, que es determinista y trazable.
- **El modelo generativo (Gemini)** se usa únicamente para **redactar** en lenguaje natural las justificaciones y los informes, a partir de la información que ya recuperó el sistema.

Cada hipótesis diagnóstica que el sistema entrega está vinculada a una entrada concreta de la base (mediante un identificador `kb_id`), de modo que siempre es posible auditar de dónde salió. Esta arquitectura reduce el riesgo de alucinación en las decisiones que importan y hace el sistema explicable, dos propiedades deseables en un CDSS.

### 3.3 El mecanismo de recuperación

La base de conocimiento contiene quince patrones diagnósticos, cada uno con sus biomarcadores, presentación clínica, factores de riesgo, patrón de imagen esperado y guía para el radiólogo. El retrieval funciona por coincidencia de términos clínicos: normaliza el texto (minúsculas, sin tildes), extrae términos significativos y puntúa cada entrada de la base según cuántos términos comparte con el caso.

Se eligió deliberadamente un método simple y transparente en lugar de uno más sofisticado (como embeddings semánticos), porque en un contexto médico la explicabilidad tiene valor propio: se puede mostrar exactamente qué términos motivaron cada hipótesis. Durante el desarrollo se detectó que ciertas palabras genéricas ("dolor", "síntomas") generaban coincidencias espurias, así que se incorporó una lista de términos vacíos de dominio (*stopwords clínicas*) que se excluyen del cálculo. Esta corrección, discutida en la sección de evaluación, eliminó los falsos positivos sin recurrir a trucos que inflaran artificialmente los resultados.

### 3.4 El contrato de datos

Las entradas y salidas del sistema están formalizadas como estructuras de datos tipadas (`dataclasses` de Python). El Componente 1 recibe un `PacienteInput` (edad, sexo, motivo de consulta, historia clínica, síntomas, factores de riesgo, biomarcadores) y devuelve un `SalidaComponente1` con las hipótesis, la decisión de imagen, la urgencia y el resumen-puente. El Componente 2 recibe un `EstudioImagenInput` (modalidad, región anatómica, hallazgos estructurados y, opcionalmente, la ruta a una imagen real) más el contexto del componente anterior, y devuelve un `SalidaComponente2` con la guía de lectura, la correlación de hallazgos, la concordancia y el informe orientado.

### 3.5 El Componente 2 y el manejo de imágenes

El Componente 2 trabaja sobre hallazgos estructurados del estudio y los correlaciona con el patrón de imagen esperado según la hipótesis del oncólogo. Adicionalmente, se implementó un modo de imagen real opcional: si se le proporciona la ruta a un archivo DICOM o a una imagen común, el sistema extrae su metadata (modalidad, región del cuerpo, dimensiones). Es importante subrayar que el sistema **no analiza los píxeles ni detecta lesiones**: orienta la lectura pero la interpretación de la imagen sigue siendo del radiólogo. Esta es una decisión de alcance consciente, coherente con el rol de herramienta de apoyo.

### 3.6 El modo simulado

El sistema depende del modelo Gemini solo para la redacción. Para garantizar que el proyecto siempre pueda ejecutarse de punta a punta —incluso sin una clave de API configurada— se implementó un modo simulado que reemplaza la redacción por plantillas construidas a partir de la propia base de conocimiento. En este modo la lógica clínica permanece intacta, porque no dependía del modelo. Así, cualquier persona puede correr y evaluar el sistema sin credenciales, y activar Gemini cuando quiera una redacción más rica. La clave de API se gestiona mediante una variable de entorno cargada desde un archivo local que está explícitamente excluido del control de versiones, de modo que nunca se expone.

## 4. Evaluación

### 4.1 Diseño del conjunto de casos

Se construyó un conjunto de dieciocho casos clínicos sintéticos con su etiqueta esperada (*ground truth*): trece casos positivos que cubren distintos tipos de cáncer y deberían derivarse a imagen, y cinco casos negativos correspondientes a cuadros benignos (cefalea tensional, control de rutina, cuadro gripal, lumbalgia mecánica, ansiedad) que no deberían generar una derivación oncológica. La inclusión de casos negativos es deliberada: permite medir si el sistema evita las derivaciones innecesarias, no solo si detecta las necesarias.

### 4.2 Métricas

Se evaluaron tres dimensiones. Para la **decisión de derivación a imagen** (tratada como una clasificación binaria donde el positivo es "requiere imagen") se calcularon precisión, recall, F1 y accuracy, junto con la matriz de confusión. Para el **diagnóstico** se midió el acierto de la hipótesis principal (top-1) en los casos positivos. Para el **triage** se midió el acierto del nivel de urgencia asignado.

### 4.3 Resultados

| Dimensión | Resultado |
|---|---|
| Derivación a imagen — Precisión / Recall / F1 / Accuracy | 1.000 / 1.000 / 1.000 / 1.000 |
| Matriz de confusión | TP=13, FP=0, TN=5, FN=0 |
| Diagnóstico top-1 (positivos) | 13/13 (1.000) |
| Urgencia / triage (positivos) | 11/13 (0.846) |

El sistema clasificó correctamente los dieciocho casos en cuanto a la decisión de derivación, sin falsos positivos ni falsos negativos, y acertó la hipótesis diagnóstica principal en todos los casos positivos. El triage falló en dos de trece casos.

### 4.4 Lectura honesta de los resultados

Estos números son altos, y es importante interpretarlos con cuidado en lugar de presentarlos como evidencia de desempeño clínico. El conjunto de casos es sintético y utiliza una terminología alineada con la de la base de conocimiento, lo que facilita la tarea del sistema. Sobre datos clínicos reales —con lenguaje libre, ambiguo y ruidoso— el rendimiento sería considerablemente menor. El valor del ejercicio no está en la magnitud de las métricas sino en el diseño del flujo de evaluación, la inclusión de casos negativos y la trazabilidad de las decisiones.

El error en el triage es ilustrativo: la urgencia se toma de la hipótesis principal y no integra el resto de la información, de modo que en dos casos (uno de próstata y uno de tiroides, ambos de urgencia intermedia) el sistema asignó un nivel distinto al esperado. Se decidió dejar este error visible en lugar de ajustar el sistema para forzar un acierto perfecto, porque documentar la limitación es más valioso que ocultarla.

## 5. Limitaciones y trabajo futuro

- El retrieval por coincidencia de términos es explicable pero no capta sinónimos ni paráfrasis; un trabajo futuro natural es incorporar embeddings semánticos manteniendo la trazabilidad.
- El modelo de urgencia es simplista (toma la de la hipótesis principal); convendría integrar varias señales.
- La base cubre quince tipos de cáncer; ampliarla requiere revisión de especialistas.
- El Componente 2 no procesa píxeles; una extensión sería integrar modelos de visión para segmentación asistida.
- Todo el trabajo se realizó con datos sintéticos, que no sustituyen la validación clínica ni la aprobación regulatoria.

## 6. Consideraciones éticas

El proyecto se mantuvo dentro del encuadre de un sistema de apoyo, sin presentarse nunca como sustituto del juicio médico. Los riesgos característicos de la IA generativa en medicina se abordaron de forma explícita: las alucinaciones se mitigaron al no delegarle al modelo la lógica clínica; el sesgo de datos se reconoce como dependiente del dataset; y la calibración de confianza se señala advirtiendo que las probabilidades expresan confianza relativa del sistema y no certeza clínica. En cuanto a la privacidad, se trabajó únicamente con datos sintéticos, y se documenta que un despliegue real exigiría anonimización y cumplimiento de los marcos vigentes (HIPAA, GDPR, Ley 26.529 en Argentina).

## 7. Conclusión

OncoBridge AI demuestra, sobre un caso acotado pero completo, cómo la IA generativa puede acercar el conocimiento oncológico al punto de decisión clínica sin desplazar al médico. La decisión de diseño más relevante —separar la lógica clínica del retrieval de la redacción del modelo— resultó ser también la más alineada con las exigencias del dominio: produjo un sistema explicable, trazable y robusto ante la ausencia del modelo generativo. El ejercicio de evaluación, con su conjunto de casos negativos y su lectura honesta de las métricas, refuerza la idea de que en IA médica el análisis crítico de las limitaciones importa tanto como el desempeño reportado.
